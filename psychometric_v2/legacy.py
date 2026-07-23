from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from psychometric_v2.models import ConstructAnchor
from psychometric_v2.taxonomy import FACETS, LEGACY_FEATURE_MAP


def read_jsonl(path: str | Path) -> list[Any]:
    with Path(path).open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def discover_legacy_anchor_file(root: str | Path) -> Path:
    root_path = Path(root)
    candidates: list[Path] = []
    for path in root_path.rglob("*.jsonl"):
        try:
            rows = read_jsonl(path)
            features = {row["feature"] for row in rows}
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
            continue
        if len(rows) == 60 and features == set(LEGACY_FEATURE_MAP):
            candidates.append(path)

    if not candidates:
        raise FileNotFoundError("no 60-item legacy Big Five JSONL was found")

    def sort_key(path: Path) -> tuple[bool, int, str]:
        path_string = str(path)
        return path.parent.name != "data", len(path_string), path_string

    return min(candidates, key=sort_key)


def migrate_anchor_file(path: str | Path) -> list[ConstructAnchor]:
    facet_numbers: defaultdict[str, int] = defaultdict(int)
    anchors: list[ConstructAnchor] = []
    for item_number, row in enumerate(read_jsonl(path), start=1):
        feature = row["feature"]
        facet_id = LEGACY_FEATURE_MAP[feature]
        facet_numbers[facet_id] += 1
        anchors.append(
            ConstructAnchor(
                anchor_id=f"bfi2-{facet_id}-{facet_numbers[facet_id]:02d}",
                item_number=item_number,
                text_zh=row["question"].strip(),
                legacy_feature=feature,
                domain_id=FACETS[facet_id].domain_id,
                facet_id=facet_id,
                reverse=row["reverse"],
            )
        )
    return anchors


def write_anchor_asset(
    anchors: Iterable[ConstructAnchor],
    destination: str | Path,
) -> None:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [anchor.model_dump(mode="json") for anchor in anchors]
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination_path.parent,
            prefix=f".{destination_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, destination_path)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def load_anchor_asset(path: str | Path) -> dict[str, ConstructAnchor]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("anchor asset must be a non-empty JSON array")

    anchors: dict[str, ConstructAnchor] = {}
    ordered_anchors: list[ConstructAnchor] = []
    for position, raw_anchor in enumerate(payload, start=1):
        try:
            anchor = ConstructAnchor.model_validate(
                raw_anchor,
                strict=True,
                extra="forbid",
            )
        except ValidationError as exc:
            raise ValueError(f"invalid anchor at position {position}: {exc}") from exc
        if anchor.anchor_id in anchors:
            raise ValueError(f"duplicate anchor_id: {anchor.anchor_id}")
        anchors[anchor.anchor_id] = anchor
        ordered_anchors.append(anchor)

    if len(ordered_anchors) != 60:
        raise ValueError("anchor asset must contain exactly 60 anchors")
    if [anchor.item_number for anchor in ordered_anchors] != list(range(1, 61)):
        raise ValueError("anchor asset item_number sequence must be exactly 1..60")
    if sum(anchor.reverse for anchor in ordered_anchors) != 30:
        raise ValueError("anchor asset must contain exactly 30 reverse anchors")

    facet_counts = Counter(anchor.facet_id for anchor in ordered_anchors)
    if len(facet_counts) != 15 or set(facet_counts) != set(FACETS):
        raise ValueError("anchor asset must cover exactly 15 facets matching FACETS")
    if set(facet_counts.values()) != {4}:
        raise ValueError("anchor asset must contain exactly 4 anchors for every facet")
    if any(anchor.source != "legacy_big_five_60" for anchor in ordered_anchors):
        raise ValueError("anchor source must be legacy_big_five_60")

    facet_numbers: defaultdict[str, int] = defaultdict(int)
    for anchor in ordered_anchors:
        facet_numbers[anchor.facet_id] += 1
        expected_id = f"bfi2-{anchor.facet_id}-{facet_numbers[anchor.facet_id]:02d}"
        if anchor.anchor_id != expected_id:
            raise ValueError(
                "anchor asset anchor_id sequence must match facet loading order"
            )
    return anchors
