from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from psychometric_v2.legacy import (  # noqa: E402
    discover_legacy_anchor_file,
    migrate_anchor_file,
    write_anchor_asset,
)


DESTINATION = ROOT / "psychometric_v2/assets/data/bfi2_anchors.json"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate the legacy Big Five anchors")
    parser.add_argument(
        "--source",
        type=Path,
        help="explicit read-only path to the legacy 60-item JSONL",
    )
    return parser.parse_args(argv)


def _source_path(explicit_source: Path | None) -> Path:
    if explicit_source is not None:
        return explicit_source
    environment_source = os.environ.get("LEGACY_ANCHOR_SOURCE")
    if environment_source:
        return Path(environment_source)
    return discover_legacy_anchor_file(ROOT)


def _reject_source_destination_alias(source: Path) -> None:
    try:
        same_file = source.samefile(DESTINATION)
    except OSError:
        same_file = source.resolve() == DESTINATION.resolve()
    if same_file:
        raise ValueError("source and destination must identify different files")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    source = _source_path(args.source)
    _reject_source_destination_alias(source)
    anchors = migrate_anchor_file(source)
    if len(anchors) != 60:
        raise ValueError("legacy anchor migration must produce exactly 60 anchors")
    if sum(anchor.reverse for anchor in anchors) != 30:
        raise ValueError("legacy anchor migration must produce exactly 30 reverse anchors")
    if len({anchor.facet_id for anchor in anchors}) != 15:
        raise ValueError("legacy anchor migration must cover exactly 15 facets")
    write_anchor_asset(anchors, DESTINATION)
    print(f"Wrote {len(anchors)} anchors to {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
