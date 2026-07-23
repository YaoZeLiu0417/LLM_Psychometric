import csv
import io
import json

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.exports import project_csv_bytes, project_json_bytes
from psychometric_v2.models import (
    GenerationMetadata,
    GenerationMode,
    ResearchProject,
)


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


def test_json_export_round_trip_preserves_live_generation_metadata() -> None:
    project = build_demo_project()
    base = project.items[project.selected_item_id]
    metadata = GenerationMetadata(
        model_id="fake-model",
        prompt_version=base.prompt_version,
        constraint_snapshot={
            "project_config": project.config.model_dump(mode="json"),
            "domain_id": base.domain_id,
            "facet_id": base.facet_id,
            "anchor_ids": list(base.anchor_ids),
            "context_domain": base.scenario_blueprint.context_domain,
        },
    )
    live = base.validated_update(
        item_id="live-export-round-trip",
        generation_mode=GenerationMode.LIVE,
        model_id=metadata.model_id,
        generation_metadata=metadata,
    )
    expanded = project.validated_update(
        items={**dict(project.items), live.item_id: live},
        selected_item_id=live.item_id,
    )

    exported = project_json_bytes(expanded)
    restored = ResearchProject.model_validate_json(exported)

    assert restored.items[live.item_id].generation_metadata == metadata
    assert restored == expanded


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


def test_csv_export_escapes_formula_prefixes_without_changing_json() -> None:
    project = build_demo_project()
    item = next(iter(project.items.values()))
    assert item.construct_spec is not None
    dangerous_anchor = "@anchor"
    dangerous_options = tuple(
        option.validated_update(option_id=option_id, text_zh=text_zh)
        for option, option_id, text_zh in zip(
            item.options,
            ("+option", "-option", "@option", "=option"),
            ("\tformula-tab", "\rformula-cr", "\nformula-lf", "safe text"),
            strict=True,
        )
    )
    dangerous_item = item.validated_update(
        item_id="=item",
        anchor_ids=(dangerous_anchor,),
        stem_zh="\tstem",
        construct_spec=item.construct_spec.validated_update(
            anchor_ids=(dangerous_anchor,)
        ),
        options=dangerous_options,
    )
    dangerous_project = project.validated_update(
        items={dangerous_item.item_id: dangerous_item},
        selected_item_id=dangerous_item.item_id,
    )

    csv_rows = list(
        csv.DictReader(
            io.StringIO(
                project_csv_bytes(dangerous_project).decode("utf-8-sig"),
                newline="",
            )
        )
    )
    json_payload = json.loads(project_json_bytes(dangerous_project))

    assert len(csv_rows) == 4
    assert all(row["item_id"] == "'=item" for row in csv_rows)
    assert all(row["anchor_ids"] == "'@anchor" for row in csv_rows)
    assert all(row["stem_zh"] == "'\tstem" for row in csv_rows)
    assert [row["option_id"] for row in csv_rows] == [
        "'+option",
        "'-option",
        "'@option",
        "'=option",
    ]
    assert [row["option_text_zh"] for row in csv_rows] == [
        "'\tformula-tab",
        "'\rformula-cr",
        "'\nformula-lf",
        "safe text",
    ]
    assert all(row["domain_id"] == item.domain_id for row in csv_rows)
    assert all(not row["score"].startswith("'") for row in csv_rows)
    assert json_payload["selected_item_id"] == "=item"
    assert json_payload["items"]["=item"]["stem_zh"] == "\tstem"
    assert json_payload["items"]["=item"]["options"][0]["option_id"] == "+option"
