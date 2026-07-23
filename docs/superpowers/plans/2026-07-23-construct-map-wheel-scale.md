# Construct Map Wheel Scale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Slightly enlarge the Construct Map wheel and keep all five OCEAN domain letters upright while preserving the approved outer-facet layout and data contracts.

**Architecture:** Change only the existing Plotly sunburst layout and orientation configuration in `construct_map.py`. Add one focused regression test beside the existing alias/hover contract, then verify the rendered SVG at desktop and narrow viewports.

**Tech Stack:** Python, Plotly, Streamlit, pytest, Streamlit AppTest

---

### Task 1: Enlarge and Reorient the Construct Map Wheel

**Files:**
- Modify: `psychometric_v2/ui/pages/construct_map.py:69-84`
- Modify: `tests/test_app_smoke.py:196-232`

- [ ] **Step 1: Write the failing Plotly layout contract test**

Add this test immediately after the existing wheel alias/hover test:

```python
def test_construct_map_wheel_uses_approved_scale_and_orientation() -> None:
    figure = construct_map._taxonomy_figure()
    trace = figure.data[0]

    assert trace.insidetextorientation == "auto"
    assert figure.layout.height == 560
    assert figure.layout.margin.to_plotly_json() == {
        "l": 4,
        "r": 4,
        "t": 4,
        "b": 4,
    }
```

- [ ] **Step 2: Run the exact test and verify RED**

Run:

```powershell
python -m pytest tests/test_app_smoke.py::test_construct_map_wheel_uses_approved_scale_and_orientation -q
```

Expected: FAIL because the current figure uses `radial`, height `520`, and margins of `8`.

- [ ] **Step 3: Apply the minimal Plotly configuration change**

In the existing `go.Sunburst` call, change only:

```python
insidetextorientation="auto",
```

In the existing `figure.update_layout` call, change only:

```python
height=560,
margin={"l": 4, "r": 4, "t": 4, "b": 4},
```

Do not alter labels, text info, customdata, hover, font sizing, uniform-text behavior, colors, ordering, hierarchy, column proportions, source rows, theme CSS, or any data file.

- [ ] **Step 4: Run focused and full automated verification**

Run:

```powershell
python -m pytest tests/test_app_smoke.py -q -k "construct_map_wheel"
python -m pytest -q
git diff --check
```

Expected: wheel tests and the complete suite report zero failures; `git diff --check` emits no errors.

- [ ] **Step 5: Self-review and commit**

Review the diff against the preserved-behavior list. Commit only the production and regression-test changes:

```powershell
git add -- psychometric_v2/ui/pages/construct_map.py tests/test_app_smoke.py
git commit -m "style: enlarge construct map wheel"
```

- [ ] **Step 6: Verify the live SVG at desktop and narrow viewports**

Restart the Streamlit service from the feature worktree so Python imports the new Plotly configuration. At `1280x720` and `760x900`, open `CONSTRUCT MAP` and inspect the rendered SVG.

Acceptance checks:

- all 20 sunburst labels have non-zero bounds and remain inside the Plotly chart container;
- the five inner-ring text transforms contain no `rotate(...)` component;
- the desktop wheel's outer path bounds are larger than the previous approximately `504px` diameter;
- `Compassion`, `Responsible`, and `Depression` are fully visible with additional radial space;
- the wheel and facet detail panel do not overlap;
- four source rows remain readable, with zero code blocks and zero copy-code controls.

Reset the temporary browser viewport after verification and keep the final `http://localhost:8502/` page available to the user.

