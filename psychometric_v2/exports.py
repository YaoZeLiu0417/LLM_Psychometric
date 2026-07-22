import csv
import io

from psychometric_v2.models import ResearchProject


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


def project_json_bytes(project: ResearchProject) -> bytes:
    return project.model_dump_json(indent=2).encode("utf-8")


def project_csv_bytes(project: ResearchProject) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for item in project.items.values():
        for option in sorted(item.options, key=lambda value: value.display_order):
            writer.writerow(
                {
                    "item_id": item.item_id,
                    "domain_id": item.domain_id,
                    "facet_id": item.facet_id,
                    "anchor_ids": "|".join(item.anchor_ids),
                    "stem_zh": item.stem_zh,
                    "option_id": option.option_id,
                    "option_text_zh": option.text_zh,
                    "trait_level": option.trait_level,
                    "score": option.score,
                    "display_order": option.display_order,
                    "evidence_status": item.evidence_status.value,
                    "generation_mode": item.generation_mode.value,
                }
            )
    return output.getvalue().encode("utf-8-sig")
