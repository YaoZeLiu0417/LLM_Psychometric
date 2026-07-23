import math
from dataclasses import replace
from xml.etree import ElementTree as ET

from psychometric_v2.taxonomy import DOMAINS, FACETS


SVG_NS = "http://www.w3.org/2000/svg"
PATH = f"{{{SVG_NS}}}path"
TEXT = f"{{{SVG_NS}}}text"
TITLE = f"{{{SVG_NS}}}title"

EXPECTED_DOMAIN_LABELS = ("E", "A", "C", "N", "O")
EXPECTED_FACET_LABELS = (
    "Social",
    "Assert",
    "Energy",
    "Compassion",
    "Respect",
    "Trust",
    "Organized",
    "Productive",
    "Responsible",
    "Anxiety",
    "Depression",
    "Volatility",
    "Curiosity",
    "Aesthetic",
    "Creative",
)
EXPECTED_ROTATIONS = (
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
EXPECTED_DOMAIN_TEXT_COLORS = (
    "#FFFFFF",
    "#0B0B0D",
    "#0B0B0D",
    "#0B0B0D",
    "#FFFFFF",
)


def _render(domains=DOMAINS, facets=FACETS) -> str:
    from psychometric_v2.ui.construct_wheel import build_construct_wheel_svg

    return build_construct_wheel_svg(domains, facets)


def _elements(root: ET.Element, tag: str, class_name: str) -> list[ET.Element]:
    return [
        element
        for element in root.findall(f".//{tag}")
        if element.attrib.get("class") == class_name
    ]


def _relative_luminance(color: str) -> float:
    channels = tuple(
        int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)
    )
    linear = tuple(
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    )
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    foreground_luminance = _relative_luminance(foreground)
    background_luminance = _relative_luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _translate_coordinates(transform: str) -> tuple[float, float]:
    translation = transform.split(" rotate(", 1)[0]
    coordinates = translation.removeprefix("translate(").removesuffix(")")
    x, y = coordinates.split()
    return float(x), float(y)


def test_svg_wheel_preserves_taxonomy_structure_colors_and_titles() -> None:
    markup = _render()
    root = ET.fromstring(markup)
    domain_paths = _elements(root, PATH, "construct-wheel__domain")
    facet_paths = _elements(root, PATH, "construct-wheel__facet")
    titles = root.findall(f".//{TITLE}")

    assert root.attrib["viewBox"] == "0 0 600 600"
    assert root.attrib["role"] == "img"
    assert "Big Five" in root.attrib["aria-label"]
    assert "青少年大五人格构念分类" in root.attrib["aria-label"]
    descriptions = root.findall(f".//{{{SVG_NS}}}desc")
    assert len(descriptions) == 1
    assert "Five Big Five domains" in descriptions[0].text
    assert "大五人格五个领域" in descriptions[0].text
    assert [path.attrib["data-domain-id"] for path in domain_paths] == list(DOMAINS)
    assert [path.attrib["data-facet-id"] for path in facet_paths] == list(FACETS)
    assert [path.attrib["fill"] for path in domain_paths] == [
        domain.color for domain in DOMAINS.values()
    ]
    assert [path.attrib["fill"] for path in facet_paths] == [
        DOMAINS[facet.domain_id].color for facet in FACETS.values()
    ]
    assert len(domain_paths) == 5
    assert len(facet_paths) == 15
    assert len(titles) == 20
    assert titles[0].text == (
        f"{next(iter(DOMAINS.values())).label_en} / "
        f"{next(iter(DOMAINS.values())).label_zh}"
    )
    assert titles[-1].text == (
        f"{next(reversed(FACETS.values())).label_en} / "
        f"{next(reversed(FACETS.values())).label_zh}"
    )
    assert all(path.find(TITLE) is not None for path in (*domain_paths, *facet_paths))
    assert all(
        path.attrib["aria-label"] == path.find(TITLE).text
        for path in (*domain_paths, *facet_paths)
    )


def test_svg_wheel_uses_approved_geometry_labels_and_rotations() -> None:
    markup = _render()
    root = ET.fromstring(markup)
    domain_paths = _elements(root, PATH, "construct-wheel__domain")
    facet_paths = _elements(root, PATH, "construct-wheel__facet")
    domain_labels = _elements(root, TEXT, "construct-wheel__domain-label")
    facet_labels = _elements(root, TEXT, "construct-wheel__facet-label")

    assert root.attrib["data-outer-radius"] == "292"
    assert root.attrib["data-domain-radius"] == "123"
    assert domain_paths[0].attrib["d"] == (
        "M 300 300 L 423 300 A 123 123 0 0 0 338.009 183.02 Z"
    )
    assert facet_paths[0].attrib["d"] == (
        "M 592 300 A 292 292 0 0 0 566.755 181.233 L 412.366 249.971 "
        "A 123 123 0 0 1 423 300 Z"
    )
    assert tuple(label.text for label in domain_labels) == EXPECTED_DOMAIN_LABELS
    assert tuple(label.text for label in facet_labels) == EXPECTED_FACET_LABELS
    assert all("rotate" not in label.attrib["transform"] for label in domain_labels)
    assert tuple(
        int(label.attrib["transform"].rsplit("rotate(", 1)[1].removesuffix(")"))
        for label in facet_labels
    ) == EXPECTED_ROTATIONS
    assert facet_labels[7].text == "Productive"
    assert facet_labels[7].attrib["transform"].endswith("rotate(0)")
    assert facet_labels[2].text == "Energy"
    assert facet_labels[2].attrib["transform"].endswith("rotate(120)")
    for index, label in enumerate(facet_labels):
        angle = math.radians(12 + index * 24)
        expected_x = 300 + 274 * math.cos(angle)
        expected_y = 300 - 274 * math.sin(angle)
        x, y = _translate_coordinates(label.attrib["transform"])

        assert abs(x - expected_x) <= 0.001
        assert abs(y - expected_y) <= 0.001


def test_svg_wheel_uses_accessible_label_contrast() -> None:
    root = ET.fromstring(_render())
    domain_paths = _elements(root, PATH, "construct-wheel__domain")
    facet_paths = _elements(root, PATH, "construct-wheel__facet")
    domain_labels = _elements(root, TEXT, "construct-wheel__domain-label")
    facet_labels = _elements(root, TEXT, "construct-wheel__facet-label")
    expected_facet_colors = tuple(
        color for color in EXPECTED_DOMAIN_TEXT_COLORS for _ in range(3)
    )

    assert tuple(
        label.attrib["fill"] for label in domain_labels
    ) == EXPECTED_DOMAIN_TEXT_COLORS
    assert tuple(
        label.attrib["fill"] for label in facet_labels
    ) == expected_facet_colors
    assert all(
        _contrast_ratio(label.attrib["fill"], path.attrib["fill"]) >= 4.5
        for label, path in zip(domain_labels, domain_paths, strict=True)
    )
    assert all(
        _contrast_ratio(label.attrib["fill"], path.attrib["fill"]) >= 4.5
        for label, path in zip(facet_labels, facet_paths, strict=True)
    )


def test_svg_wheel_is_continuous_and_escapes_dynamic_content() -> None:
    unsafe = replace(
        DOMAINS["extraversion"],
        label_en='Extra <unsafe> & "quoted"',
        label_zh="外向 & 测试",
        color="#123456",
    )
    domains = dict(DOMAINS)
    domains["extraversion"] = unsafe
    unsafe_facet = replace(
        FACETS["sociability"],
        label_en='Social <unsafe> & "quoted"',
        label_zh="社交 & 测试",
    )
    facets = dict(FACETS)
    facets["sociability"] = unsafe_facet

    markup = _render(domains, facets)
    root = ET.fromstring(markup)
    first_domain = _elements(root, PATH, "construct-wheel__domain")[0]
    first_facet = _elements(root, PATH, "construct-wheel__facet")[0]

    assert "\n" not in markup
    assert "<unsafe>" not in markup
    assert "&lt;unsafe&gt;" in markup
    assert first_domain.attrib["fill"] == "#123456"
    assert first_domain.attrib["aria-label"] == (
        'Extra <unsafe> & "quoted" / 外向 & 测试'
    )
    assert first_domain.find(TITLE).text == first_domain.attrib["aria-label"]
    assert first_facet.attrib["aria-label"] == (
        'Social <unsafe> & "quoted" / 社交 & 测试'
    )
    assert first_facet.find(TITLE).text == first_facet.attrib["aria-label"]
