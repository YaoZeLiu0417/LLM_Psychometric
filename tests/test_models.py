import pytest
from pydantic import ValidationError

from psychometric_v2.models import CandidateItem, EvidenceStatus, ResponseOption


def make_option(score: int, order: int) -> ResponseOption:
    return ResponseOption(
        option_id=f"o{score}",
        text_zh=f"行为选项{score}",
        trait_level=score,
        score=score,
        display_order=order,
        rationale=f"可观察行为水平{score}",
        desirability_note="无明显道德优劣",
    )


def test_candidate_requires_four_unique_score_levels() -> None:
    item = CandidateItem(
        item_id="item-1",
        domain_id="extraversion",
        facet_id="sociability",
        anchor_ids=["bfi2-sociability-01"],
        instruction_zh="如果是你，你最可能怎么做？",
        stem_zh="一次社团活动开始前，几位同学还不熟悉彼此。",
        options=[
            make_option(4, 1),
            make_option(1, 2),
            make_option(3, 3),
            make_option(2, 4),
        ],
        evidence_status=EvidenceStatus.MODEL_DRAFT,
    )
    assert {option.score for option in item.options} == {1, 2, 3, 4}


def test_candidate_rejects_duplicate_scores() -> None:
    with pytest.raises(ValidationError):
        CandidateItem(
            item_id="item-1",
            domain_id="extraversion",
            facet_id="sociability",
            anchor_ids=["bfi2-sociability-01"],
            instruction_zh="如果是你，你最可能怎么做？",
            stem_zh="一次社团活动开始前，几位同学还不熟悉彼此。",
            options=[
                make_option(1, 1),
                make_option(1, 2),
                make_option(3, 3),
                make_option(4, 4),
            ],
        )


def test_validated_is_not_an_allowed_evidence_status() -> None:
    assert "VALIDATED" not in {status.value for status in EvidenceStatus}
