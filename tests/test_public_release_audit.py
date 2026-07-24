import os
import subprocess
from pathlib import Path

from scripts.audit_public_release import audit_repository, scan_content


def test_scan_content_accepts_documented_placeholders() -> None:
    assert scan_content(
        ".env.example",
        (
            b"OPENAI_API_KEY=your-key\n"
            b"LIVE_ACCESS_CODE=choose-a-strong-code\n"
            b"OPENAI_BASE_URL=optional-compatible-endpoint\n"
        ),
    ) == ()


def test_scan_content_accepts_consecutive_blank_secret_assignments() -> None:
    assert scan_content(
        ".env.example",
        b"OPENAI_API_KEY=\nLIVE_ACCESS_CODE=\n",
    ) == ()


def test_scan_content_flags_secret_values_and_personal_paths() -> None:
    credential = b"sk" + b"-" + (b"x" * 32)
    assignment = b"LIVE_ACCESS" + b"_CODE=real-secret-value"
    personal_path = b"C:\\" + b"Users\\private-user\\Desktop\\notes.txt"

    findings = scan_content(
        "historical.txt",
        credential + b"\n" + assignment + b"\n" + personal_path,
    )

    assert {finding.rule for finding in findings} == {
        "credential-shape",
        "nonempty-secret-assignment",
        "personal-path",
    }
    assert all("real-secret-value" not in finding.description for finding in findings)
    assert all(credential.decode() not in finding.description for finding in findings)


def test_scan_content_skips_binary_and_oversized_payloads() -> None:
    credential = b"sk" + b"-" + (b"x" * 32)

    assert scan_content("font.ttf", b"\x00\x01\x02" + credential) == ()
    assert scan_content("large.txt", b"x" * (5 * 1024 * 1024 + 1)) == ()


def test_scanner_source_does_not_match_its_pattern_literals() -> None:
    source = Path("scripts/audit_public_release.py").read_bytes()

    assert scan_content("scripts/audit_public_release.py", source) == ()


def test_historical_scanner_regex_literal_is_not_a_personal_path() -> None:
    historical_literal = b're.compile(rb"/' + b'Users/[^/\\s]+")'

    assert scan_content(
        "history:old-object:scripts/audit_public_release.py",
        historical_literal,
    ) == ()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Audit Test",
        "GIT_AUTHOR_EMAIL": "audit@example.invalid",
        "GIT_COMMITTER_NAME": "Audit Test",
        "GIT_COMMITTER_EMAIL": "audit@example.invalid",
    }
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=environment,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_audit_finds_deleted_reachable_secret_blob(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    (tmp_path / "README.md").write_text("clean\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "clean")

    secret = "OPENAI_API_KEY=" + "sk" + "-" + ("x" * 32) + "\n"
    secret_path = tmp_path / "historical-secret.txt"
    secret_path.write_text(secret, encoding="utf-8")
    _git(tmp_path, "add", "historical-secret.txt")
    _git(tmp_path, "commit", "-m", "add historical secret")
    secret_path.unlink()
    _git(tmp_path, "add", "-u")
    _git(tmp_path, "commit", "-m", "delete historical secret")

    findings = audit_repository(tmp_path)

    credential_findings = tuple(
        finding
        for finding in findings
        if finding.rule == "credential-shape"
    )
    assert credential_findings
    assert any(
        "historical-secret.txt" in finding.source
        for finding in credential_findings
    )
    assert all(secret.strip() not in finding.description for finding in findings)


def test_audit_flags_tracked_secret_file_by_path(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    secret_dir = tmp_path / ".streamlit"
    secret_dir.mkdir()
    (secret_dir / "secrets.toml").write_text("placeholder = true\n", encoding="utf-8")
    _git(tmp_path, "add", ".streamlit/secrets.toml")
    _git(tmp_path, "commit", "-m", "track forbidden secret file")

    findings = audit_repository(tmp_path)

    assert any(finding.rule == "secret-file" for finding in findings)
