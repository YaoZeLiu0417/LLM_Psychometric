from collections.abc import Mapping

import pytest

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import CandidateItem, ResponseOption
from psychometric_v2.quality import run_deterministic_checks


CHECK_IDS = (
    "OPTION_COUNT",
    "SCORE_COVERAGE",
    "DISPLAY_ORDER",
    "DUPLICATE_OPTIONS",
    "OPTION_LENGTH_BALANCE",
    "PROVENANCE",
)


def construct_invalid_candidate(
    item: CandidateItem, **updates: object
) -> CandidateItem:
    values = {
        name: getattr(item, name)
        for name in CandidateItem.model_fields
    }
    values.update(updates)
    return CandidateItem.model_construct(**values)


def check_map(item: CandidateItem) -> Mapping[str, object]:
    return {check.check_id: check for check in run_deterministic_checks(item)}


def test_seed_checks_are_fixed_complete_and_actionable() -> None:
    project = build_demo_project()

    for item in project.items.values():
        checks = run_deterministic_checks(item)
        assert tuple(check.check_id for check in checks) == CHECK_IDS
        assert checks == item.quality_checks
        assert all(check.evidence.strip() for check in checks)
        assert all(check.recommendation.strip() for check in checks)
        assert all(
            check.outcome.value == "PASS"
            for check in checks
            if check.severity.value == "ERROR"
        )


@pytest.mark.parametrize(
    ("check_id", "updates"),
    [
        ("OPTION_COUNT", lambda item: {"options": item.options[:3]}),
        (
            "SCORE_COVERAGE",
            lambda item: {
                "options": (
                    item.options[0].model_copy(update={"score": 4, "trait_level": 4}),
                    *item.options[1:],
                )
            },
        ),
        (
            "DISPLAY_ORDER",
            lambda item: {
                "options": (
                    item.options[0].model_copy(update={"display_order": 2}),
                    *item.options[1:],
                )
            },
        ),
        (
            "DUPLICATE_OPTIONS",
            lambda item: {
                "options": (
                    item.options[0],
                    item.options[1].model_copy(update={"text_zh": f" {item.options[0].text_zh} "}),
                    *item.options[2:],
                )
            },
        ),
    ],
    ids=["count", "score-coverage", "display-order", "duplicate-text"],
)
def test_structural_failures_are_error_flags(
    check_id: str, updates: object
) -> None:
    item = next(iter(build_demo_project().items.values()))
    invalid = construct_invalid_candidate(item, **updates(item))  # type: ignore[operator]

    check = check_map(invalid)[check_id]

    assert check.severity.value == "ERROR"
    assert check.outcome.value == "FLAG"
    assert check.evidence.strip()
    assert check.recommendation.strip()


@pytest.mark.parametrize(
    "updates",
    [
        {"anchor_ids": ()},
        {"construct_spec": None},
        {"scenario_blueprint": None},
    ],
    ids=["empty-anchors", "missing-spec", "missing-blueprint"],
)
def test_provenance_requires_anchors_spec_and_blueprint(
    updates: dict[str, object]
) -> None:
    item = next(iter(build_demo_project().items.values()))
    invalid = construct_invalid_candidate(item, **updates)

    check = check_map(invalid)["PROVENANCE"]

    assert check.severity.value == "ERROR"
    assert check.outcome.value == "FLAG"


def test_provenance_requires_matching_domain_facet_and_anchors() -> None:
    item = next(iter(build_demo_project().items.values()))
    assert item.construct_spec is not None
    mismatched_spec = item.construct_spec.model_construct(
        domain_id="agreeableness",
        facet_id="respectfulness",
        anchor_ids=("other-anchor",),
        definition_zh=item.construct_spec.definition_zh,
        behavioral_indicators=item.construct_spec.behavioral_indicators,
        exclusions=item.construct_spec.exclusions,
        potential_confounds=item.construct_spec.potential_confounds,
    )
    invalid = construct_invalid_candidate(item, construct_spec=mismatched_spec)

    assert check_map(invalid)["PROVENANCE"].outcome.value == "FLAG"


@pytest.mark.parametrize(
    ("longest_length", "expected_outcome"),
    [(22, "PASS"), (23, "FLAG")],
)
def test_option_length_balance_flags_only_above_2_point_2(
    longest_length: int, expected_outcome: str
) -> None:
    item = next(iter(build_demo_project().items.values()))
    lengths = (10, 10, 10, longest_length)
    options = tuple(
        ResponseOption(
            option_id=f"length-{index}",
            text_zh=chr(96 + index) * length,
            trait_level=index,
            score=index,
            display_order=index,
            rationale=f"level {index}",
            desirability_note="neutral",
        )
        for index, length in enumerate(lengths, start=1)
    )
    candidate = construct_invalid_candidate(item, options=options)

    check = check_map(candidate)["OPTION_LENGTH_BALANCE"]

    assert check.severity.value == "WARNING"
    assert check.outcome.value == expected_outcome
    assert str(longest_length) in check.evidence
    assert "10" in check.evidence
