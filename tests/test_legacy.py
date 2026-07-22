from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

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


def test_load_anchor_asset_rejects_duplicate_anchor_ids(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    asset = tmp_path / "duplicates.json"
    write_jsonl(source, make_legacy_rows())
    anchor = legacy_module().migrate_anchor_file(source)[0]
    payload = anchor.model_dump(mode="json")
    asset.write_text(json.dumps([payload, payload]), encoding="utf-8")

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
    source = tmp_path / "source.jsonl"
    asset = tmp_path / "damaged.json"
    write_jsonl(source, make_legacy_rows())
    anchor = legacy_module().migrate_anchor_file(source)[0]
    payload = anchor.model_dump(mode="json")
    payload["domain_id"] = "agreeableness"
    asset.write_text(json.dumps([payload]), encoding="utf-8")

    with pytest.raises(ValidationError):
        legacy_module().load_anchor_asset(asset)


def test_cli_accepts_explicit_read_only_source(tmp_path: Path, monkeypatch) -> None:
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
