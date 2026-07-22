from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

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
        relative = path.relative_to(root_path)
        return path.parent.name != "data", len(relative.parts), relative.as_posix()

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
    destination_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_anchor_asset(path: str | Path) -> dict[str, ConstructAnchor]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("anchor asset must be a non-empty JSON array")

    anchors: dict[str, ConstructAnchor] = {}
    for raw_anchor in payload:
        anchor = ConstructAnchor.model_validate(
            raw_anchor,
            strict=True,
            extra="forbid",
        )
        if anchor.anchor_id in anchors:
            raise ValueError(f"duplicate anchor_id: {anchor.anchor_id}")
        anchors[anchor.anchor_id] = anchor
    return anchors
