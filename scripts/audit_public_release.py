from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


_MAX_TEXT_BYTES = 5 * 1024 * 1024
_CREDENTIAL_PATTERNS = (
    re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\bAKIA[A-Z0-9]{16}\b"),
)
_SECRET_ASSIGNMENT = re.compile(
    rb"(?im)^\s*(?:export\s+)?"
    rb"(?P<name>[A-Z][A-Z0-9_]*(?:API_KEY|ACCESS_CODE|TOKEN|SECRET|PASSWORD))"
    rb"\s*=\s*(?P<value>[^\r\n#]*)"
)
_PERSONAL_PATH_PATTERNS = (
    re.compile(rb"(?i)\b[A-Z]:\\Users\\[^\\\r\n]+"),
    re.compile(rb"(?i)/Users/[^/\s]+"),
    re.compile(rb"(?i)/home/[^/\s]+"),
)
_PLACEHOLDER_MARKERS = (
    "<",
    "your-",
    "your_",
    "choose-",
    "replace-",
    "example",
    "placeholder",
    "test-only",
    "fake-",
)
_FORBIDDEN_SECRET_FILES = {".env", "secrets.toml"}


@dataclass(frozen=True)
class Finding:
    rule: str
    source: str
    description: str


class AuditRuntimeError(RuntimeError):
    pass


def _placeholder_assignment(value: bytes) -> bool:
    normalized = value.decode("utf-8", errors="ignore").strip().strip("'\"")
    if not normalized:
        return True
    lowered = normalized.lower()
    return any(lowered.startswith(marker) or marker in lowered for marker in _PLACEHOLDER_MARKERS)


def scan_content(source: str, content: bytes) -> tuple[Finding, ...]:
    if len(content) > _MAX_TEXT_BYTES or b"\x00" in content:
        return ()

    findings: list[Finding] = []
    if any(pattern.search(content) for pattern in _CREDENTIAL_PATTERNS):
        findings.append(
            Finding(
                rule="credential-shape",
                source=source,
                description="Credential-shaped value detected; matched text is redacted.",
            )
        )

    if any(
        not _placeholder_assignment(match.group("value"))
        for match in _SECRET_ASSIGNMENT.finditer(content)
    ):
        findings.append(
            Finding(
                rule="nonempty-secret-assignment",
                source=source,
                description="Non-placeholder secret assignment detected; value is redacted.",
            )
        )

    if any(pattern.search(content) for pattern in _PERSONAL_PATH_PATTERNS):
        findings.append(
            Finding(
                rule="personal-path",
                source=source,
                description="User-specific filesystem path detected; matched path is redacted.",
            )
        )
    return tuple(findings)


def _git(
    repo: Path,
    *args: str,
    input_bytes: bytes | None = None,
) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AuditRuntimeError(f"Git command failed: {' '.join(args)}")
    return completed.stdout


def _secret_file_finding(source: str, path: str) -> Finding | None:
    normalized = PurePosixPath(path.replace("\\", "/"))
    name = normalized.name.lower()
    if name not in _FORBIDDEN_SECRET_FILES:
        return None
    if name == ".env" and normalized.name.lower() == ".env.example":
        return None
    return Finding(
        rule="secret-file",
        source=source,
        description="Secret-bearing filename is tracked in Git; content is not shown.",
    )


def _reachable_objects(repo: Path) -> tuple[tuple[str, str], ...]:
    objects: list[tuple[str, str]] = []
    for raw_line in _git(repo, "rev-list", "--objects", "--all").splitlines():
        oid_bytes, separator, path_bytes = raw_line.partition(b" ")
        oid = oid_bytes.decode("ascii", errors="strict")
        path = path_bytes.decode("utf-8", errors="replace") if separator else ""
        objects.append((oid, path))
    return tuple(objects)


def _object_metadata(
    repo: Path,
    object_ids: tuple[str, ...],
) -> dict[str, tuple[str, int]]:
    if not object_ids:
        return {}
    request = ("\n".join(object_ids) + "\n").encode("ascii")
    response = _git(repo, "cat-file", "--batch-check", input_bytes=request)
    metadata: dict[str, tuple[str, int]] = {}
    for line in response.decode("ascii", errors="strict").splitlines():
        parts = line.split()
        if len(parts) != 3 or not parts[2].isdigit():
            continue
        metadata[parts[0]] = (parts[1], int(parts[2]))
    return metadata


def audit_repository(repo: Path) -> tuple[Finding, ...]:
    root_text = _git(repo.resolve(), "rev-parse", "--show-toplevel")
    root = Path(root_text.decode("utf-8", errors="strict").strip()).resolve()
    findings: set[Finding] = set()

    tracked_paths = tuple(
        path.decode("utf-8", errors="replace")
        for path in _git(root, "ls-files", "-z").split(b"\x00")
        if path
    )
    for tracked_path in tracked_paths:
        source = f"worktree:{tracked_path}"
        secret_file = _secret_file_finding(source, tracked_path)
        if secret_file is not None:
            findings.add(secret_file)
        file_path = root / Path(tracked_path)
        if file_path.is_file():
            findings.update(scan_content(source, file_path.read_bytes()))

    reachable = _reachable_objects(root)
    object_ids = tuple(dict.fromkeys(oid for oid, _path in reachable))
    metadata = _object_metadata(root, object_ids)
    blob_cache: dict[str, bytes] = {}
    for oid, historical_path in reachable:
        object_type, size = metadata.get(oid, ("", 0))
        if object_type != "blob":
            continue
        display_path = historical_path or "<unknown-path>"
        source = f"history:{oid}:{display_path}"
        secret_file = _secret_file_finding(source, historical_path)
        if secret_file is not None:
            findings.add(secret_file)
        if size > _MAX_TEXT_BYTES:
            continue
        content = blob_cache.get(oid)
        if content is None:
            content = _git(root, "cat-file", "blob", oid)
            blob_cache[oid] = content
        findings.update(scan_content(source, content))

    return tuple(
        sorted(
            findings,
            key=lambda finding: (
                finding.rule,
                finding.source,
                finding.description,
            ),
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit the worktree and every reachable Git blob before public release."
    )
    parser.add_argument("--repo", type=Path, default=Path("."))
    arguments = parser.parse_args(argv)
    try:
        findings = audit_repository(arguments.repo)
    except (AuditRuntimeError, OSError, UnicodeError):
        print("Public release audit could not run.")
        return 2

    if findings:
        print(f"Public release audit failed with {len(findings)} finding(s):")
        for finding in findings:
            print(f"[{finding.rule}] {finding.source}: {finding.description}")
        return 1

    print("Public release audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
