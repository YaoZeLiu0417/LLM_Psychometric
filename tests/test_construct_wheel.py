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


def _render(domains=DOMAINS, facets=FACETS) -> str:
    from psychometric_v2.ui.construct_wheel import build_construct_wheel_svg

    return build_construct_wheel_svg(domains, facets)


def _elements(root: ET.Element, tag: str, class_name: str) -> list[ET.Element]:
    return [
        element
        for element in root.findall(f".//{tag}")
        if element.attrib.get("class") == class_name
    ]


def test_svg_wheel_preserves_taxonomy_structure_colors_and_titles() -> None:
    markup = _render()
    root = ET.fromstring(markup)
    domain_paths = _elements(root, PATH, "construct-wheel__domain")
    facet_paths = _elements(root, PATH, "construct-wheel__facet")
    titles = root.findall(f".//{TITLE}")

    assert root.attrib["viewBox"] == "0 0 600 600"
    assert root.attrib["role"] == "img"
    assert "Big Five" in root.attrib["aria-label"]
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
    assert domain_paths[0].attrib["d"].startswith(
        "M 300 300 L 423 300 A 123 123 0 0 0"
    )
    assert facet_paths[0].attrib["d"].startswith(
        "M 592 300 A 292 292 0 0 0"
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


def test_svg_wheel_is_continuous_and_escapes_dynamic_content() -> None:
    unsafe = replace(
        DOMAINS["extraversion"],
        label_en='Extra <unsafe> & "quoted"',
        label_zh="外向 & 测试",
    )
    domains = dict(DOMAINS)
    domains["extraversion"] = unsafe

    markup = _render(domains, FACETS)
    root = ET.fromstring(markup)
    first_domain = _elements(root, PATH, "construct-wheel__domain")[0]

    assert "\n" not in markup
    assert "<unsafe>" not in markup
    assert "&lt;unsafe&gt;" in markup
    assert first_domain.attrib["aria-label"] == (
        'Extra <unsafe> & "quoted" / 外向 & 测试'
    )
    assert first_domain.find(TITLE).text == first_domain.attrib["aria-label"]
