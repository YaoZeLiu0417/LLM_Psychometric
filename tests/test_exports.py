import csv
import io
import json

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.exports import project_csv_bytes, project_json_bytes


CSV_COLUMNS = (
    "item_id",
    "domain_id",
    "facet_id",
    "anchor_ids",
    "stem_zh",
    "option_id",
    "option_text_zh",
    "trait_level",
    "score",
    "display_order",
    "evidence_status",
    "generation_mode",
)


def test_json_export_is_complete_utf8_project_without_preview_responses() -> None:
    project = build_demo_project()

    exported = project_json_bytes(project)
    decoded = exported.decode("utf-8")
    payload = json.loads(decoded)

    assert exported == project.model_dump_json(indent=2).encode("utf-8")
    assert payload["config"]["project_id"] == project.config.project_id
    for item_id, item_payload in payload["items"].items():
        item = project.items[item_id]
        assert item_payload["anchor_ids"] == list(item.anchor_ids)
        assert item_payload["construct_spec"]["domain_id"] == item.domain_id
        assert item_payload["construct_spec"]["facet_id"] == item.facet_id
        assert item_payload["construct_spec"]["anchor_ids"] == list(item.anchor_ids)
        assert item_payload["scenario_blueprint"] is not None
    assert "participant" not in decoded.lower()
    assert "preview_responses" not in decoded.lower()


def test_csv_export_has_bom_exact_columns_and_ordered_option_rows() -> None:
    project = build_demo_project()

    exported = project_csv_bytes(project)
    text = exported.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)

    assert exported.startswith(b"\xef\xbb\xbf")
    assert tuple(reader.fieldnames or ()) == CSV_COLUMNS
    assert len(rows) == 20

    expected_rows = []
    for item in project.items.values():
        for option in sorted(item.options, key=lambda candidate: candidate.display_order):
            expected_rows.append(
                (
                    item.item_id,
                    option.option_id,
                    str(option.display_order),
                    str(option.score),
                )
            )
    assert [
        (row["item_id"], row["option_id"], row["display_order"], row["score"])
        for row in rows
    ] == expected_rows

    for row in rows:
        item = project.items[row["item_id"]]
        assert row["anchor_ids"] == "|".join(item.anchor_ids)
        assert row["evidence_status"] == "MODEL_DRAFT"
        assert row["generation_mode"] == "CURATED DEMO"

    for item in project.items.values():
        item_rows = [row for row in rows if row["item_id"] == item.item_id]
        assert {int(row["score"]) for row in item_rows} == {1, 2, 3, 4}
