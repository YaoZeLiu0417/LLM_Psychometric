from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from psychometric_v2.taxonomy import FACETS, LEGACY_FEATURE_MAP


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = REPO_ROOT / "psychometric_v2/assets/data/bfi2_anchors.json"
SCRIPT_PATH = REPO_ROOT / "scripts/migrate_legacy_anchors.py"


def legacy_module():
    return importlib.import_module("psychometric_v2.legacy")


def make_legacy_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for round_number in range(1, 5):
        for feature in LEGACY_FEATURE_MAP:
            rows.append(
                {
                    "question": f"  中文题目 {round_number}: {feature}  ",
                    "feature": feature,
                    "reverse": len(rows) % 2 == 1,
                }
            )
    return rows


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(f"{payload}\n\n", encoding="utf-8")


def make_anchor_payloads(tmp_path: Path) -> list[dict[str, object]]:
    source = tmp_path / "payload-source.jsonl"
    write_jsonl(source, make_legacy_rows())
    return [
        anchor.model_dump(mode="json")
        for anchor in legacy_module().migrate_anchor_file(source)
    ]


def write_asset(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_script_module():
    spec = importlib.util.spec_from_file_location("migrate_legacy_anchors", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_jsonl_reads_nonempty_utf8_lines(tmp_path: Path) -> None:
    source = tmp_path / "anchors.jsonl"
    source.write_text(
        '\n{"question": "中文一", "feature": "特征", "reverse": false}\n\n'
        '{"question": "中文二", "feature": "特征", "reverse": true}\n',
        encoding="utf-8",
    )

    rows = legacy_module().read_jsonl(source)

    assert [row["question"] for row in rows] == ["中文一", "中文二"]
    assert [row["reverse"] for row in rows] == [False, True]


def test_discovery_prefers_a_file_whose_parent_is_data(tmp_path: Path) -> None:
    rows = make_legacy_rows()
    write_jsonl(tmp_path / "short.jsonl", rows)
    preferred = tmp_path / "nested" / "data" / "preferred.jsonl"
    write_jsonl(preferred, rows)
    write_jsonl(tmp_path / "ignored.txt", rows)
    (tmp_path / "broken.jsonl").write_bytes(b"\xff")
    (tmp_path / "invalid.jsonl").write_text("not JSON\n", encoding="utf-8")
    wrong_rows = rows.copy()
    wrong_rows[0] = {**wrong_rows[0], "feature": "unknown"}
    write_jsonl(tmp_path / "wrong-feature.jsonl", wrong_rows)

    discovered = legacy_module().discover_legacy_anchor_file(tmp_path)

    assert discovered == preferred


def test_discovery_uses_shortest_path_then_lexical_order(tmp_path: Path) -> None:
    rows = make_legacy_rows()
    lexical_first = tmp_path / "a.jsonl"
    write_jsonl(tmp_path / "b.jsonl", rows)
    write_jsonl(lexical_first, rows)
    write_jsonl(tmp_path / "nested" / "c.jsonl", rows)

    assert legacy_module().discover_legacy_anchor_file(tmp_path) == lexical_first


def test_discovery_compares_full_path_string_length_before_lexical_order(
    tmp_path: Path,
) -> None:
    rows = make_legacy_rows()
    shorter = tmp_path / "z.jsonl"
    write_jsonl(tmp_path / "aa.jsonl", rows)
    write_jsonl(shorter, rows)

    assert legacy_module().discover_legacy_anchor_file(tmp_path) == shorter


def test_discovery_raises_exact_error_when_no_candidate_exists(tmp_path: Path) -> None:
    write_jsonl(tmp_path / "only-59.jsonl", make_legacy_rows()[:-1])

    with pytest.raises(
        FileNotFoundError,
        match="^no 60-item legacy Big Five JSONL was found$",
    ):
        legacy_module().discover_legacy_anchor_file(tmp_path)


def test_migrate_anchor_file_preserves_order_and_numbers_each_facet(
    tmp_path: Path,
) -> None:
    source = tmp_path / "legacy.jsonl"
    rows = make_legacy_rows()
    write_jsonl(source, rows)

    anchors = legacy_module().migrate_anchor_file(source)

    assert [anchor.item_number for anchor in anchors] == list(range(1, 61))
    assert [anchor.legacy_feature for anchor in anchors] == [
        row["feature"] for row in rows
    ]
    assert [anchor.reverse for anchor in anchors] == [row["reverse"] for row in rows]
    for facet_id, facet in FACETS.items():
        facet_anchors = [anchor for anchor in anchors if anchor.facet_id == facet_id]
        assert [anchor.anchor_id for anchor in facet_anchors] == [
            f"bfi2-{facet_id}-{number:02d}" for number in range(1, 5)
        ]
        assert {anchor.domain_id for anchor in facet_anchors} == {facet.domain_id}
        assert all(anchor.source == "legacy_big_five_60" for anchor in facet_anchors)
        assert all(anchor.text_zh == anchor.text_zh.strip() for anchor in facet_anchors)


def test_write_and_load_anchor_asset_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    destination = tmp_path / "new" / "data" / "anchors.json"
    write_jsonl(source, make_legacy_rows())
    anchors = legacy_module().migrate_anchor_file(source)

    legacy_module().write_anchor_asset(anchors, destination)
    loaded = legacy_module().load_anchor_asset(destination)

    assert "中文题目" in destination.read_text(encoding="utf-8")
    assert list(loaded) == [anchor.anchor_id for anchor in anchors]
    assert list(loaded.values()) == anchors
    assert set(destination.parent.iterdir()) == {destination}


def test_write_anchor_asset_preserves_destination_and_cleans_temp_on_replace_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "data" / "anchors.json"
    destination.parent.mkdir(parents=True)
    destination.write_text("original asset", encoding="utf-8")
    before_files = set(destination.parent.iterdir())
    replace_calls: list[tuple[Path, Path]] = []

    def fail_replace(source: str | Path, target: str | Path) -> None:
        replace_calls.append((Path(source), Path(target)))
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", fail_replace)
    source = tmp_path / "source.jsonl"
    write_jsonl(source, make_legacy_rows())
    anchors = legacy_module().migrate_anchor_file(source)

    with pytest.raises(OSError, match="replace failed"):
        legacy_module().write_anchor_asset(anchors, destination)

    assert destination.read_text(encoding="utf-8") == "original asset"
    assert set(destination.parent.iterdir()) == before_files
    assert len(replace_calls) == 1
    assert replace_calls[0][0].parent == destination.parent
    assert replace_calls[0][1] == destination


def test_load_anchor_asset_rejects_duplicate_anchor_ids(tmp_path: Path) -> None:
    asset = tmp_path / "duplicates.json"
    payload = make_anchor_payloads(tmp_path)
    payload[1]["anchor_id"] = payload[0]["anchor_id"]
    write_asset(asset, payload)

    with pytest.raises(ValueError, match="duplicate anchor_id"):
        legacy_module().load_anchor_asset(asset)


@pytest.mark.parametrize("payload", [[], {}, None])
def test_load_anchor_asset_rejects_empty_or_non_array_json(
    tmp_path: Path,
    payload: object,
) -> None:
    asset = tmp_path / "invalid-shape.json"
    asset.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        legacy_module().load_anchor_asset(asset)


def test_load_anchor_asset_rejects_damaged_provenance(tmp_path: Path) -> None:
    asset = tmp_path / "damaged.json"
    payload = make_anchor_payloads(tmp_path)
    payload[0]["domain_id"] = "agreeableness"
    write_asset(asset, payload)

    with pytest.raises(ValueError, match="invalid anchor at position 1"):
        legacy_module().load_anchor_asset(asset)


def test_load_anchor_asset_requires_exactly_60_anchors(tmp_path: Path) -> None:
    asset = tmp_path / "short.json"
    write_asset(asset, make_anchor_payloads(tmp_path)[:-1])

    with pytest.raises(ValueError, match="exactly 60 anchors"):
        legacy_module().load_anchor_asset(asset)


@pytest.mark.parametrize("corruption", ["duplicate", "out-of-order"])
def test_load_anchor_asset_requires_sequential_item_numbers(
    tmp_path: Path,
    corruption: str,
) -> None:
    asset = tmp_path / f"item-numbers-{corruption}.json"
    payload = make_anchor_payloads(tmp_path)
    if corruption == "duplicate":
        payload[1]["item_number"] = payload[0]["item_number"]
    else:
        payload[0], payload[1] = payload[1], payload[0]
    write_asset(asset, payload)

    with pytest.raises(ValueError, match="item_number sequence"):
        legacy_module().load_anchor_asset(asset)


def test_load_anchor_asset_requires_exactly_30_reverse_anchors(
    tmp_path: Path,
) -> None:
    asset = tmp_path / "reverse-count.json"
    payload = make_anchor_payloads(tmp_path)
    payload[0]["reverse"] = not payload[0]["reverse"]
    write_asset(asset, payload)

    with pytest.raises(ValueError, match="exactly 30 reverse anchors"):
        legacy_module().load_anchor_asset(asset)


def test_load_anchor_asset_requires_four_anchors_for_every_facet(
    tmp_path: Path,
) -> None:
    asset = tmp_path / "facet-count.json"
    payload = make_anchor_payloads(tmp_path)
    replacement = payload[0].copy()
    replacement.update(
        anchor_id="bfi2-sociability-05",
        item_number=payload[-1]["item_number"],
        reverse=payload[-1]["reverse"],
    )
    payload[-1] = replacement
    write_asset(asset, payload)

    with pytest.raises(ValueError, match="exactly 4 anchors for every facet"):
        legacy_module().load_anchor_asset(asset)


def test_load_anchor_asset_requires_canonical_source(tmp_path: Path) -> None:
    asset = tmp_path / "source.json"
    payload = make_anchor_payloads(tmp_path)
    payload[0]["source"] = "untrusted_source"
    write_asset(asset, payload)

    with pytest.raises(ValueError, match="source must be legacy_big_five_60"):
        legacy_module().load_anchor_asset(asset)


def test_load_anchor_asset_requires_facet_local_anchor_id_sequence(
    tmp_path: Path,
) -> None:
    asset = tmp_path / "anchor-id.json"
    payload = make_anchor_payloads(tmp_path)
    payload[0]["anchor_id"] = "bfi2-sociability-99"
    write_asset(asset, payload)

    with pytest.raises(ValueError, match="anchor_id sequence"):
        legacy_module().load_anchor_asset(asset)


def test_cli_accepts_explicit_read_only_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "external" / "legacy.jsonl"
    destination = tmp_path / "repo" / "anchors.json"
    write_jsonl(source, make_legacy_rows())
    before = source.read_bytes()
    script = load_script_module()
    monkeypatch.setattr(script, "DESTINATION", destination)

    result = script.main(["--source", str(source)])

    assert result == 0
    assert source.read_bytes() == before
    loaded = legacy_module().load_anchor_asset(destination)
    assert len(loaded) == 60


def test_cli_rejects_destination_equal_to_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "legacy.jsonl"
    write_jsonl(source, make_legacy_rows())
    before = source.read_bytes()
    script = load_script_module()
    monkeypatch.setattr(script, "DESTINATION", source)

    with pytest.raises(ValueError, match="source and destination"):
        script.main(["--source", str(source)])

    assert source.read_bytes() == before


@pytest.mark.parametrize("alias_kind", ["hardlink", "symlink"])
def test_cli_rejects_destination_alias_of_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    alias_kind: str,
) -> None:
    source = tmp_path / "legacy.jsonl"
    destination = tmp_path / "anchors.json"
    write_jsonl(source, make_legacy_rows())
    if alias_kind == "hardlink":
        os.link(source, destination)
    else:
        try:
            destination.symlink_to(source)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")
    before = source.read_bytes()
    script = load_script_module()
    monkeypatch.setattr(script, "DESTINATION", destination)

    with pytest.raises(ValueError, match="source and destination"):
        script.main(["--source", str(source)])

    assert source.read_bytes() == before


def test_packaged_anchor_asset_has_expected_inventory() -> None:
    anchors = list(legacy_module().load_anchor_asset(ASSET_PATH).values())

    assert len(anchors) == 60
    assert sum(anchor.reverse for anchor in anchors) == 30
    assert {anchor.facet_id for anchor in anchors} == set(FACETS)
    assert {anchor.domain_id for anchor in anchors} == {
        facet.domain_id for facet in FACETS.values()
    }
    assert [anchor.item_number for anchor in anchors] == list(range(1, 61))
    assert anchors[0].text_zh == "我是一个性格外向，喜欢交际的人。"
    assert anchors[0].legacy_feature == "外向性、社交"
    assert all(
        sum(anchor.facet_id == facet_id for anchor in anchors) == 4
        for facet_id in FACETS
    )
