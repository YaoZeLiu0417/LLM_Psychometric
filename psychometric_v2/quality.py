from psychometric_v2.models import (
    CandidateItem,
    CheckOutcome,
    CheckSeverity,
    QualityCheck,
)


def _check(
    check_id: str,
    label: str,
    severity: CheckSeverity,
    passed: bool,
    evidence: str,
    recommendation: str,
) -> QualityCheck:
    return QualityCheck(
        check_id=check_id,
        label=label,
        severity=severity,
        outcome=CheckOutcome.PASS if passed else CheckOutcome.FLAG,
        evidence=evidence,
        recommendation=recommendation,
    )


def run_deterministic_checks(item: CandidateItem) -> tuple[QualityCheck, ...]:
    options = item.options
    option_count_ok = len(options) == 4

    scores = [option.score for option in options]
    score_coverage_ok = (
        sorted(scores) == [1, 2, 3, 4]
        and all(option.trait_level == option.score for option in options)
    )

    display_orders = [option.display_order for option in options]
    display_order_ok = sorted(display_orders) == [1, 2, 3, 4]

    normalized_ids = [option.option_id.strip() for option in options]
    normalized_texts = [option.text_zh.strip() for option in options]
    unique_options_ok = (
        bool(options)
        and all(normalized_ids)
        and all(normalized_texts)
        and len(set(normalized_ids)) == len(normalized_ids)
        and len(set(normalized_texts)) == len(normalized_texts)
    )

    lengths = [len(text) for text in normalized_texts]
    shortest = min(lengths, default=0)
    longest = max(lengths, default=0)
    ratio = longest / shortest if shortest else float("inf")
    length_balance_ok = bool(lengths) and ratio <= 2.2
    ratio_text = f"{ratio:.2f}" if ratio != float("inf") else "infinite"

    spec = item.construct_spec
    anchors_ok = bool(item.anchor_ids) and all(
        anchor_id.strip() for anchor_id in item.anchor_ids
    )
    spec_ok = (
        spec is not None
        and spec.domain_id == item.domain_id
        and spec.facet_id == item.facet_id
        and spec.anchor_ids == item.anchor_ids
    )
    blueprint_ok = item.scenario_blueprint is not None
    provenance_ok = anchors_ok and spec_ok and blueprint_ok

    return (
        _check(
            "OPTION_COUNT",
            "选项数量",
            CheckSeverity.ERROR,
            option_count_ok,
            f"检测到 {len(options)} 个选项；要求恰好 4 个。",
            "保持四个选项；若被标记，请补齐或删除选项至恰好四个。",
        ),
        _check(
            "SCORE_COVERAGE",
            "分数覆盖",
            CheckSeverity.ERROR,
            score_coverage_ok,
            f"当前分数为 {scores}；要求各覆盖 1、2、3、4 且 trait_level 与 score 一致。",
            "保持 1 至 4 各一个分数，并将每个 trait_level 设为对应 score。",
        ),
        _check(
            "DISPLAY_ORDER",
            "显示顺序",
            CheckSeverity.ERROR,
            display_order_ok,
            f"当前 display_order 为 {display_orders}；要求各覆盖 1、2、3、4。",
            "为四个选项分配不重复的 display_order 1 至 4。",
        ),
        _check(
            "DUPLICATE_OPTIONS",
            "重复选项",
            CheckSeverity.ERROR,
            unique_options_ok,
            "选项 ID 和去除首尾空白后的文本均唯一。"
            if unique_options_ok
            else "检测到空白或重复的选项 ID/文本。",
            "保持每个选项 ID 和行为文本非空且彼此不同。",
        ),
        _check(
            "OPTION_LENGTH_BALANCE",
            "选项长度平衡",
            CheckSeverity.WARNING,
            length_balance_ok,
            f"最短选项 {shortest} 字符，最长选项 {longest} 字符，长度比为 {ratio_text}；阈值为 2.20。",
            "保持最长与最短选项的字符数比不超过 2.2；若被标记，请缩短最长项或补充最短项。",
        ),
        _check(
            "PROVENANCE",
            "来源完整性",
            CheckSeverity.ERROR,
            provenance_ok,
            (
                f"anchors_nonempty={anchors_ok}, spec_matches={spec_ok}, "
                f"blueprint_present={blueprint_ok}。"
            ),
            "保留非空 anchor_ids，并确保 construct_spec 的 domain、facet、anchors 与题目一致且 scenario_blueprint 存在。",
        ),
    )
