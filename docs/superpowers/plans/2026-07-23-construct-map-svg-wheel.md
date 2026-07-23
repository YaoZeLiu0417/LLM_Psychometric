# Construct Map Responsive SVG Wheel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Construct Map Plotly Sunburst with a responsive, accessible SVG wheel whose domain ring is 42% of the radius and whose fifteen facet labels all read from the outer edge toward the center.

**Architecture:** Add one pure Python SVG renderer under `psychometric_v2/ui/` and keep Streamlit layout in `construct_map.py`. The renderer consumes the existing immutable taxonomy mappings, builds escaped XML with the standard library, and exposes deterministic geometry for unit tests; the page only injects the returned SVG markup.

**Tech Stack:** Python 3.11, `xml.etree.ElementTree`, Streamlit, pytest, Streamlit AppTest

---

## File Structure

- Create `psychometric_v2/ui/construct_wheel.py`: own wheel constants, polar geometry, XML construction, short labels, fixed facet rotations, hover titles, and accessibility metadata.
- Create `tests/test_construct_wheel.py`: parse real SVG output and verify structure, order, geometry, rotations, labels, colors, tooltips, and escaping.
- Modify `psychometric_v2/ui/pages/construct_map.py`: remove Plotly-only code and render the SVG while preserving the selector, detail panel, source anchors, and session state.
- Modify `tests/test_app_smoke.py`: replace Plotly graph-object assertions with an AppTest integration assertion for the SVG markup; retain all source-row regression coverage.

### Task 1: Build The Pure SVG Renderer

**Files:**
- Create: `psychometric_v2/ui/construct_wheel.py`
- Create: `tests/test_construct_wheel.py`

- [ ] **Step 1: Write the failing SVG contract tests**

Create `tests/test_construct_wheel.py` with the following complete content. Imports occur inside `_render()` so the tests fail in the test body because the requested module does not yet exist, rather than failing during collection.

```python
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
    assert titles[0].text == f"{next(iter(DOMAINS.values())).label_en} / {next(iter(DOMAINS.values())).label_zh}"
    assert titles[-1].text == f"{next(reversed(FACETS.values())).label_en} / {next(reversed(FACETS.values())).label_zh}"
    assert all(path.find(TITLE) is not None for path in (*domain_paths, *facet_paths))
    assert all(path.attrib["aria-label"] == path.find(TITLE).text for path in (*domain_paths, *facet_paths))


def test_svg_wheel_uses_approved_geometry_labels_and_rotations() -> None:
    markup = _render()
    root = ET.fromstring(markup)
    domain_paths = _elements(root, PATH, "construct-wheel__domain")
    facet_paths = _elements(root, PATH, "construct-wheel__facet")
    domain_labels = _elements(root, TEXT, "construct-wheel__domain-label")
    facet_labels = _elements(root, TEXT, "construct-wheel__facet-label")

    assert root.attrib["data-outer-radius"] == "292"
    assert root.attrib["data-domain-radius"] == "123"
    assert domain_paths[0].attrib["d"].startswith("M 300 300 L 423 300 A 123 123 0 0 0")
    assert facet_paths[0].attrib["d"].startswith("M 592 300 A 292 292 0 0 0")
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
    assert first_domain.attrib["aria-label"] == 'Extra <unsafe> & "quoted" / 外向 & 测试'
    assert first_domain.find(TITLE).text == first_domain.attrib["aria-label"]
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```powershell
python -m pytest tests/test_construct_wheel.py -q
```

Expected: all three tests fail from `ModuleNotFoundError: No module named 'psychometric_v2.ui.construct_wheel'`. This is the expected failure because the requested renderer does not exist yet.

- [ ] **Step 3: Implement the minimal renderer**

Create `psychometric_v2/ui/construct_wheel.py` with the following complete content:

```python
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
        f"A {_n(outer_radius)} {_n(outer_radius)} 0 0 0 {_n(outer_end_x)} {_n(outer_end_y)} "
        f"L {_n(inner_end_x)} {_n(inner_end_y)} "
        f"A {_n(inner_radius)} {_n(inner_radius)} 0 0 1 {_n(inner_start_x)} {_n(inner_start_y)} Z"
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
            path_data=_wedge_path(_DOMAIN_RADIUS, start_angle, start_angle + domain_step),
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
                "fill": "#FFFFFF",
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
                "fill": "#FFFFFF",
                "font-size": "19",
                "font-weight": "600",
                "letter-spacing": "0",
                "pointer-events": "none",
            },
        ).text = _FACET_WHEEL_LABELS[facet_id]

    return ET.tostring(root, encoding="unicode", short_empty_elements=True)
```

- [ ] **Step 4: Run the SVG tests and verify GREEN**

Run:

```powershell
python -m pytest tests/test_construct_wheel.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Run adjacent taxonomy tests and commit Task 1**

Run:

```powershell
python -m pytest tests/test_construct_wheel.py tests/test_taxonomy.py -q
git diff --check
```

Expected: all selected tests pass and `git diff --check` prints nothing.

Commit:

```powershell
git add -- psychometric_v2/ui/construct_wheel.py tests/test_construct_wheel.py
git commit -m "feat: add responsive construct wheel renderer"
```

### Task 2: Integrate The SVG With Construct Map

**Files:**
- Modify: `psychometric_v2/ui/pages/construct_map.py`
- Modify: `tests/test_app_smoke.py`

- [ ] **Step 1: Replace Plotly contract tests with an SVG AppTest contract**

In `tests/test_app_smoke.py`, add this import beside the other standard-library imports:

```python
from xml.etree import ElementTree as ET
```

Delete `test_construct_map_wheel_uses_compact_labels_and_bilingual_hover` and `test_construct_map_wheel_uses_approved_scale_and_orientation`. Insert this test in their place:

```python
def test_construct_map_renders_responsive_svg_wheel() -> None:
    app = _run_app("CONSTRUCT MAP")

    assert not app.exception
    wheel_markup = next(
        element.value
        for element in app.markdown
        if '<svg xmlns="http://www.w3.org/2000/svg" class="construct-wheel"' in element.value
    )
    root = ET.fromstring(wheel_markup)
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    assert root.attrib["viewBox"] == "0 0 600 600"
    assert root.attrib["data-outer-radius"] == "292"
    assert root.attrib["data-domain-radius"] == "123"
    assert len(root.findall("svg:path", namespace)) == 20
    assert len(root.findall(".//svg:title", namespace)) == 20
```

- [ ] **Step 2: Run the new AppTest contract and verify RED**

Run:

```powershell
python -m pytest tests/test_app_smoke.py::test_construct_map_renders_responsive_svg_wheel -q
```

Expected: FAIL because the current page still renders a Plotly chart and no `construct-wheel` SVG exists in `app.markdown`.

- [ ] **Step 3: Replace only the Construct Map chart renderer**

In `psychometric_v2/ui/pages/construct_map.py`:

1. Delete `import plotly.graph_objects as go`.
2. Add this import with the other project imports:

```python
from psychometric_v2.ui.construct_wheel import build_construct_wheel_svg
```

3. Delete `_DOMAIN_WHEEL_LABELS`, `_FACET_WHEEL_LABELS`, and `_taxonomy_figure()` in full. The new renderer now owns those responsibilities.
4. Replace the Plotly block inside `with chart_column:`:

```python
        st.plotly_chart(
            _taxonomy_figure(),
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
            key="v2_construct_sunburst",
        )
```

with:

```python
        st.markdown(
            build_construct_wheel_svg(DOMAINS, FACETS),
            unsafe_allow_html=True,
        )
```

Do not change `_source_list_markup()`, the column ratio, the selector, session state, detail cards, or anchor filtering.

- [ ] **Step 4: Run focused integration and source-row tests and verify GREEN**

Run:

```powershell
python -m pytest tests/test_app_smoke.py::test_construct_map_renders_responsive_svg_wheel tests/test_app_smoke.py::test_construct_map_source_markup_is_continuous_and_escaped tests/test_app_smoke.py::test_construct_map_renders_all_source_anchors_without_code_markup -q
```

Expected: `4 passed` because the source markup test is parameterized into two cases.

- [ ] **Step 5: Run the full suite and commit Task 2**

Run:

```powershell
python -m pytest -q
git diff --check
```

Expected: all tests pass with the existing single skip, and `git diff --check` prints nothing.

Commit:

```powershell
git add -- psychometric_v2/ui/pages/construct_map.py tests/test_app_smoke.py
git commit -m "feat: render construct map as responsive svg"
```

### Task 3: Controller Verification And Browser Acceptance

**Files:**
- Verify only; no planned source changes.

- [ ] **Step 1: Verify repository scope and fresh full test evidence**

Run:

```powershell
git status --short
git diff 4a4a53c..HEAD --stat
git diff --check 4a4a53c..HEAD
python -m pytest -q
```

Expected: the implementation plan plus the two production files and two test files from Tasks 1-2 changed after the design commit; the worktree is clean; all tests pass with one skip.

- [ ] **Step 2: Restart the Streamlit process on port 8502**

Stop only the process currently listening on port `8502`, start `streamlit run app_v2.py --server.port 8502 --server.headless true`, and wait until `http://localhost:8502` responds. Restarting is required because Streamlit may retain imported modules in the existing process.

- [ ] **Step 3: Complete browser acceptance at both approved viewports**

At `1280x720` and `760x900`, verify all of the following against the rendered page:

- one square SVG is centered and contained in the chart column;
- five domain paths, fifteen facet paths, and twenty segment titles exist;
- the `123 / 292` domain-radius ratio is approximately 42%;
- `E`, `A`, `C`, `N`, and `O` have translation-only transforms;
- the fifteen facet transforms use `168, 144, 120, 96, 72, 48, 24, 0, -24, -48, -72, -96, -120, -144, -168` in taxonomy order;
- every word begins near the outer circumference and proceeds toward the center;
- `Compassion`, `Responsible`, and `Depression` are complete and contained;
- the wheel does not overlap or compress the detail panel;
- all four source rows remain readable;
- the page contains no raw HTML block or copy-code control.

Capture one screenshot at each viewport as acceptance evidence.
