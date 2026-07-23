# Construct Map Visual Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every Construct Map wheel label readable and render all four source anchors as styled content instead of exposed HTML.

**Architecture:** Keep the existing Plotly sunburst and Streamlit page layout. Add page-local presentation aliases for chart labels while retaining formal bilingual names in hover data, and isolate source-list HTML in a pure escaped markup helper so indentation cannot trigger Markdown code-block parsing.

**Tech Stack:** Python, Streamlit, Plotly, pytest, Streamlit AppTest

---

### Task 1: Repair Construct Map Labels and Source Markup

**Files:**
- Modify: `psychometric_v2/ui/pages/construct_map.py`
- Modify: `tests/test_app_smoke.py`

- [ ] **Step 1: Write failing tests for wheel aliases and bilingual hover data**

Import `ConstructAnchor` with the existing model types, and import the page module alongside the existing generation and review imports:

```python
from psychometric_v2.models import (
    CandidateItem,
    ConstructAnchor,
    GenerationMetadata,
    GenerationMode,
    ReviewAction,
)
from psychometric_v2.ui.pages import construct_map, generation, review
```

Add a test that defines the approved visible-label tuple in taxonomy order, then checks the Plotly trace contract:

```python
def test_construct_map_wheel_uses_compact_labels_and_bilingual_hover() -> None:
    figure = construct_map._taxonomy_figure()
    trace = figure.data[0]

    assert tuple(trace.labels) == (
        "E", "A", "C", "N", "O",
        "Social", "Assert", "Energy",
        "Compassion", "Respect", "Trust",
        "Organized", "Productive", "Responsible",
        "Anxiety", "Depression", "Volatility",
        "Curiosity", "Aesthetic", "Creative",
    )
    assert tuple(trace.customdata[0]) == ("Extraversion", "外向性")
    assert tuple(trace.customdata[8]) == ("Compassion", "同情")
    assert tuple(trace.customdata[-1]) == ("Creative Imagination", "创造想象")
    assert trace.textinfo == "label"
    assert trace.hovertemplate == (
        "<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>"
    )
```

- [ ] **Step 2: Write failing tests for continuous escaped source-list HTML**

Add a pure-helper test using a constructed anchor containing HTML metacharacters:

```python
def test_construct_map_source_markup_is_continuous_and_escaped() -> None:
    anchor = ConstructAnchor.model_construct(
        anchor_id="anchor-<unsafe>",
        item_number=1,
        text_zh="<script>alert('x')</script>",
        legacy_feature="外向性、社交",
        domain_id="extraversion",
        facet_id="sociability",
        reverse=True,
        source="test",
    )

    markup = construct_map._source_list_markup((anchor,))

    assert re.search(r"(?m)^[ \t]{4,}<", markup) is None
    assert markup.count('<div class="source-row">') == 1
    assert "anchor-&lt;unsafe&gt;" in markup
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in markup
    assert "REVERSE KEYED" in markup
```

Extend the real-page smoke coverage so all default Sociability anchors are present in a single unindented source-list payload:

```python
def test_construct_map_renders_all_source_anchors_without_code_markup() -> None:
    app = _run_app("CONSTRUCT MAP")

    assert not app.exception
    source_markup = next(
        element.value for element in app.markdown if "source-list" in element.value
    )
    assert re.search(r"(?m)^[ \t]{4,}<", source_markup) is None
    assert source_markup.count('<div class="source-row">') == 4
    for suffix in ("01", "02", "03", "04"):
        assert f"bfi2-sociability-{suffix}" in source_markup
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run:

```powershell
python -m pytest tests/test_app_smoke.py -q -k "construct_map_wheel or construct_map_source"
```

Expected: the alias test fails because the trace still contains formal labels and no explicit `textinfo`; the helper tests fail because `_source_list_markup` does not exist.

- [ ] **Step 4: Add explicit presentation-only label mappings**

In `construct_map.py`, add complete page-local mappings keyed by taxonomy ID:

```python
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
```

Build `labels` from these mappings in the existing domain/facet iteration order. Do not alter IDs, parents, values, colors, or `customdata`. Set `textinfo="label"` on `go.Sunburst`; keep the formal bilingual `hovertemplate` unchanged.

- [ ] **Step 5: Add the pure source-list markup helper and use it from render**

Add this helper near `_e`:

```python
def _source_list_markup(anchors: tuple[ConstructAnchor, ...] | list[ConstructAnchor]) -> str:
    rows = []
    for anchor in anchors:
        direction = "REVERSE KEYED" if anchor.reverse else "FORWARD KEYED"
        direction_class = "status-flag" if anchor.reverse else "status-review"
        rows.append(
            f'<div class="source-row">'
            f'<div class="source-id">{_e(anchor.anchor_id)}</div>'
            f'<div class="source-text zh-content">{_e(anchor.text_zh)}</div>'
            f'<div><span class="status-badge {direction_class}">{direction}</span></div>'
            f'</div>'
        )
    return f'<div class="source-list">{"".join(rows)}</div>'
```

Replace the indented multiline `rows` generator and wrapper in `render` with:

```python
st.markdown(_source_list_markup(facet_anchors), unsafe_allow_html=True)
```

Keep `facet_anchors` sorted by source item number and continue escaping every dynamic anchor value.

- [ ] **Step 6: Run focused and full automated verification**

Run:

```powershell
python -m pytest tests/test_app_smoke.py -q -k "construct_map_wheel or construct_map_source"
python -m pytest -q
git diff --check
```

Expected: focused tests pass, the complete suite reports zero failures, and `git diff --check` emits no errors.

- [ ] **Step 7: Verify the live page at desktop and narrow widths**

Reload `http://localhost:8501/`, open `CONSTRUCT MAP`, and inspect the Plotly text nodes plus the rendered source rows at `1280x720` and a narrow viewport near `760x900`.

Verify all 20 wheel labels have non-zero rendered bounds and remain inside the Plotly chart container. Verify there is no visible raw `<div class="source-row">`, no code-copy button, four `.source-row` elements exist, and hovering representative domain and facet segments exposes complete English and Chinese names. Capture screenshots for visual inspection, then reset any temporary viewport override.

- [ ] **Step 8: Self-review and commit the implementation**

Review the diff for scope, naming, escaped dynamic values, and accidental taxonomy changes. Commit only the implementation and regression tests:

```powershell
git add -- psychometric_v2/ui/pages/construct_map.py tests/test_app_smoke.py
git commit -m "fix: refine construct map rendering"
```
