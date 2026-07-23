from __future__ import annotations

import math
from collections.abc import Mapping
from xml.etree import ElementTree as ET

from psychometric_v2.taxonomy import DomainDefinition, FacetDefinition


_SVG_NS = "http://www.w3.org/2000/svg"
_CENTER = 300.0
_OUTER_RADIUS = 292.0
_DOMAIN_RADIUS = 123.0
_DOMAIN_LABEL_RADIUS = 74.0
_FACET_LABEL_RADIUS = 274.0

_DOMAIN_WHEEL_LABELS = {
    "extraversion": "E",
    "agreeableness": "A",
    "conscientiousness": "C",
    "negative_emotionality": "N",
    "open_mindedness": "O",
}
_DOMAIN_TEXT_COLORS = {
    "extraversion": "#FFFFFF",
    "agreeableness": "#0B0B0D",
    "conscientiousness": "#0B0B0D",
    "negative_emotionality": "#0B0B0D",
    "open_mindedness": "#FFFFFF",
}
_FACET_WHEEL_LABELS = {
    "sociability": "Social",
    "assertiveness": "Assert",
    "energy_level": "Energy",
    "compassion": "Compassion",
    "respectfulness": "Respect",
    "trust": "Trust",
    "organization": "Organized",
    "productiveness": "Productive",
    "responsibility": "Responsible",
    "anxiety": "Anxiety",
    "depression": "Depression",
    "emotional_volatility": "Volatility",
    "intellectual_curiosity": "Curiosity",
    "aesthetic_sensitivity": "Aesthetic",
    "creative_imagination": "Creative",
}
_FACET_ROTATIONS = (
    168,
    144,
    120,
    96,
    72,
    48,
    24,
    0,
    -24,
    -48,
    -72,
    -96,
    -120,
    -144,
    -168,
)


def _n(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _point(radius: float, angle: float) -> tuple[float, float]:
    radians = math.radians(angle)
    return (
        _CENTER + radius * math.cos(radians),
        _CENTER - radius * math.sin(radians),
    )


def _wedge_path(radius: float, start_angle: float, end_angle: float) -> str:
    start_x, start_y = _point(radius, start_angle)
    end_x, end_y = _point(radius, end_angle)
    return (
        f"M {_n(_CENTER)} {_n(_CENTER)} "
        f"L {_n(start_x)} {_n(start_y)} "
        f"A {_n(radius)} {_n(radius)} 0 0 0 {_n(end_x)} {_n(end_y)} Z"
    )


def _annular_path(
    inner_radius: float,
    outer_radius: float,
    start_angle: float,
    end_angle: float,
) -> str:
    outer_start_x, outer_start_y = _point(outer_radius, start_angle)
    outer_end_x, outer_end_y = _point(outer_radius, end_angle)
    inner_end_x, inner_end_y = _point(inner_radius, end_angle)
    inner_start_x, inner_start_y = _point(inner_radius, start_angle)
    return (
        f"M {_n(outer_start_x)} {_n(outer_start_y)} "
        f"A {_n(outer_radius)} {_n(outer_radius)} 0 0 0 "
        f"{_n(outer_end_x)} {_n(outer_end_y)} "
        f"L {_n(inner_end_x)} {_n(inner_end_y)} "
        f"A {_n(inner_radius)} {_n(inner_radius)} 0 0 1 "
        f"{_n(inner_start_x)} {_n(inner_start_y)} Z"
    )


def _formal_name(label_en: str, label_zh: str) -> str:
    return f"{label_en} / {label_zh}"


def _segment(
    root: ET.Element,
    *,
    class_name: str,
    data_name: str,
    data_value: str,
    path_data: str,
    color: str,
    accessible_name: str,
) -> None:
    path = ET.SubElement(
        root,
        "path",
        {
            "class": class_name,
            data_name: data_value,
            "d": path_data,
            "fill": color,
            "stroke": "#F7F7F5",
            "stroke-width": "2",
            "aria-label": accessible_name,
        },
    )
    ET.SubElement(path, "title").text = accessible_name


def build_construct_wheel_svg(
    domains: Mapping[str, DomainDefinition],
    facets: Mapping[str, FacetDefinition],
) -> str:
    root = ET.Element(
        "svg",
        {
            "xmlns": _SVG_NS,
            "class": "construct-wheel",
            "viewBox": "0 0 600 600",
            "preserveAspectRatio": "xMidYMid meet",
            "role": "img",
            "aria-label": "Big Five construct taxonomy / 青少年大五人格构念分类",
            "data-outer-radius": _n(_OUTER_RADIUS),
            "data-domain-radius": _n(_DOMAIN_RADIUS),
            "style": (
                "display:block;width:100%;max-width:600px;height:auto;margin:0 auto;"
                "font-family:'Source Sans 3',sans-serif;overflow:visible"
            ),
        },
    )
    ET.SubElement(root, "desc").text = (
        "Five Big Five domains and fifteen source-anchored facets / "
        "大五人格五个领域与十五个可溯源子维度"
    )

    domain_step = 360.0 / len(domains)
    facet_step = 360.0 / len(facets)

    for index, (domain_id, domain) in enumerate(domains.items()):
        start_angle = index * domain_step
        _segment(
            root,
            class_name="construct-wheel__domain",
            data_name="data-domain-id",
            data_value=domain_id,
            path_data=_wedge_path(
                _DOMAIN_RADIUS, start_angle, start_angle + domain_step
            ),
            color=domain.color,
            accessible_name=_formal_name(domain.label_en, domain.label_zh),
        )

    for index, (facet_id, facet) in enumerate(facets.items()):
        start_angle = index * facet_step
        _segment(
            root,
            class_name="construct-wheel__facet",
            data_name="data-facet-id",
            data_value=facet_id,
            path_data=_annular_path(
                _DOMAIN_RADIUS,
                _OUTER_RADIUS,
                start_angle,
                start_angle + facet_step,
            ),
            color=domains[facet.domain_id].color,
            accessible_name=_formal_name(facet.label_en, facet.label_zh),
        )

    for index, domain_id in enumerate(domains):
        angle = index * domain_step + domain_step / 2
        x, y = _point(_DOMAIN_LABEL_RADIUS, angle)
        ET.SubElement(
            root,
            "text",
            {
                "class": "construct-wheel__domain-label",
                "x": "0",
                "y": "0",
                "transform": f"translate({_n(x)} {_n(y)})",
                "text-anchor": "middle",
                "dominant-baseline": "middle",
                "fill": _DOMAIN_TEXT_COLORS[domain_id],
                "font-size": "22",
                "font-weight": "700",
                "letter-spacing": "0",
                "pointer-events": "none",
            },
        ).text = _DOMAIN_WHEEL_LABELS[domain_id]

    for index, facet_id in enumerate(facets):
        angle = index * facet_step + facet_step / 2
        x, y = _point(_FACET_LABEL_RADIUS, angle)
        rotation = _FACET_ROTATIONS[index]
        ET.SubElement(
            root,
            "text",
            {
                "class": "construct-wheel__facet-label",
                "x": "0",
                "y": "0",
                "transform": f"translate({_n(x)} {_n(y)}) rotate({rotation})",
                "text-anchor": "start",
                "dominant-baseline": "middle",
                "fill": _DOMAIN_TEXT_COLORS[facets[facet_id].domain_id],
                "font-size": "19",
                "font-weight": "600",
                "letter-spacing": "0",
                "pointer-events": "none",
            },
        ).text = _FACET_WHEEL_LABELS[facet_id]

    return ET.tostring(root, encoding="unicode", short_empty_elements=True)
