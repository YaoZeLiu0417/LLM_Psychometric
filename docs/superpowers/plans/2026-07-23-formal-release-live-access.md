# Formal Release Polish and Protected Live Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove prototype-facing labels and duplicate Project content while protecting every live model call with a session-scoped access code.

**Architecture:** Add a small pure-Python access-code boundary that reads `LIVE_ACCESS_CODE` and performs constant-time verification. Keep the current Streamlit generation pipeline intact, but gate its UI and its server-side execution branch with session authorization. Consolidate Project identity into the existing global header and reduce the Project page to metrics, research lineage, and archived evidence.

**Tech Stack:** Python 3.12, Streamlit 1.45+, pytest, Streamlit AppTest, standard-library `hmac` and `os`.

---

## File Map

- Create `psychometric_v2/live_access.py`: environment lookup and constant-time access-code verification only.
- Create `tests/test_live_access.py`: focused unit tests for configured, missing, matching, and mismatching codes.
- Modify `psychometric_v2/ui/state.py`: initialize the session authorization state.
- Modify `psychometric_v2/ui/components.py`: render one formal header with Project-only metadata and no development badges.
- Modify `psychometric_v2/ui/pages/project.py`: remove the duplicate identity panel and revise archived-study language.
- Modify `psychometric_v2/ui/pages/generation.py`: remove the visible mode selector, render the unlock flow, and guard the live branch.
- Modify `psychometric_v2/ui/theme.py`: style the integrated metadata row and quiet evidence footnote; remove obsolete panel and badge styles.
- Modify `app_v2.py`: call the simplified header API and stop computing a header-only availability flag.
- Modify `tests/test_app_smoke.py`: enforce the formal language, consolidated layout, unlock flow, and server-side generation gate.
- Modify `.env.example`: document `LIVE_ACCESS_CODE` without a value.

### Task 1: Add the access-code boundary

**Files:**
- Create: `psychometric_v2/live_access.py`
- Create: `tests/test_live_access.py`
- Modify: `.env.example`

- [ ] **Step 1: Write failing access-code tests**

```python
from psychometric_v2.live_access import (
    live_access_configured,
    verify_live_access_code,
)


def test_live_access_is_unconfigured_without_a_secret(monkeypatch) -> None:
    monkeypatch.delenv("LIVE_ACCESS_CODE", raising=False)

    assert live_access_configured() is False
    assert verify_live_access_code("anything") is False


def test_live_access_rejects_the_wrong_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")

    assert live_access_configured() is True
    assert verify_live_access_code("wrong-code") is False


def test_live_access_accepts_the_configured_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")

    assert verify_live_access_code("job-talk-2026") is True
```

- [ ] **Step 2: Run the tests and confirm the missing-module failure**

Run: `python -m pytest tests/test_live_access.py -q`

Expected: collection fails because `psychometric_v2.live_access` does not exist.

- [ ] **Step 3: Implement the minimal verifier**

```python
from __future__ import annotations

import hmac
import os


def _configured_code() -> str:
    return os.getenv("LIVE_ACCESS_CODE", "").strip()


def live_access_configured() -> bool:
    return bool(_configured_code())


def verify_live_access_code(submitted: str) -> bool:
    configured = _configured_code()
    candidate = submitted.strip()
    return bool(configured) and hmac.compare_digest(candidate, configured)
```

Append this non-secret line to `.env.example`:

```dotenv
LIVE_ACCESS_CODE=
```

- [ ] **Step 4: Run the focused tests**

Run: `python -m pytest tests/test_live_access.py tests/test_environment.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit the access boundary**

```powershell
git add -- psychometric_v2/live_access.py tests/test_live_access.py .env.example
git commit -m "feat: add live generation access verifier"
```

### Task 2: Consolidate the Project identity and evidence layout

**Files:**
- Modify: `tests/test_app_smoke.py`
- Modify: `psychometric_v2/ui/components.py`
- Modify: `psychometric_v2/ui/pages/project.py`
- Modify: `psychometric_v2/ui/theme.py`
- Modify: `app_v2.py`

- [ ] **Step 1: Replace the old Project and header expectations with failing tests**

Update the Project expectations to:

```python
PAGES = {
    "PROJECT": (
        "2023 COLLEGE STUDENT STUDY -> 2026 ADOLESCENT RECONSTRUCTION -> FUTURE VALIDATION",
        "2023 STUDY / COLLEGE STUDENT SAMPLE",
        "Historical summary from the 2023 college-student study; raw response data are no longer available.",
    ),
    "CONSTRUCT MAP": (
        "CONSTRUCT TAXONOMY",
        "Source anchors guide content; the facet is the generation unit.",
        "SOURCE ANCHORS",
    ),
    "GENERATION STUDIO": (
        "CONSTRUCT SPECIFICATION",
        "SCENARIO BLUEPRINT",
        "RESPONSE OPTIONS",
        "QUALITY CHECKS",
        "PROVENANCE",
    ),
    "REVIEW": ("REVIEW QUEUE", "PROVENANCE", "MODEL_DRAFT"),
    "PARTICIPANT VIEW": (
        "如果是你，你最可能怎么做？",
        "新学期社团第一次活动",
    ),
}
```

Replace the startup and Project assertions with:

```python
def test_app_starts_without_exposing_development_badges(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    app = _run_app()
    markdown = _markdown(app)

    assert not app.exception
    assert "Adolescent Big Five" in markdown
    assert "CURATED DEMO" not in markdown
    assert "LIVE AVAILABLE" not in markdown
    assert "LIVE UNAVAILABLE" not in markdown


def test_project_page_uses_one_identity_panel_and_college_study_language() -> None:
    app = _run_app("PROJECT")
    markdown = _markdown(app)

    assert not app.exception
    assert markdown.count('class="top-shell"') == 1
    assert 'class="project-band"' not in markdown
    assert markdown.count("Adolescent Big Five Situational Judgment Workbench") == 1
    assert "AGE 12-15" in markdown
    assert "LOCALE zh-CN" in markdown
    assert "Mainland Chinese junior-secondary students" in markdown
    assert "Candidate item development" not in markdown
    assert "Openness item-total r" not in markdown
    assert "not evidence for V2" not in markdown
```

Change the metric assertion from `CURATED CANDIDATES` to `REFERENCE ITEMS`, while retaining the value `5`.

- [ ] **Step 2: Run the focused tests and confirm they fail on the old labels and duplicate panel**

Run: `python -m pytest tests/test_app_smoke.py -q -k "starts_without or project_page or project_curated_candidate_metric or review_header"`

Expected: failures mention `CURATED DEMO`, `project-band`, the old evidence text, and the old metric label.

- [ ] **Step 3: Simplify the header API and markup**

Change `render_header` to remove `live_available` and build optional Project metadata from the effective page:

```python
def render_header(project: ResearchProject) -> None:
    metadata = ""
    if _effective_page() == "PROJECT":
        config = project.config
        metadata = f"""
        <div class="top-meta">
          <span>AGE {_e(config.age_min)}-{_e(config.age_max)}</span>
          <span>LOCALE {_e(config.locale)}</span>
          <span>{_e(config.population)}</span>
        </div>
        """
    st.markdown(
        f"""
        <header class="top-shell">
          <div class="top-eyebrow">PSYCHOMETRIC RESEARCH WORKBENCH</div>
          <div class="top-title">Adolescent Big Five</div>
          <div class="top-subtitle">{_e(project.config.title)}</div>
          {metadata}
        </header>
        """,
        unsafe_allow_html=True,
    )
```

Delete `_effective_mode`, the badge markup, and the now-unused mode calculation. In `app_v2.py`, delete the header-only `live_available` calculation and call:

```python
render_header(research_project)
```

- [ ] **Step 4: Remove the duplicate Project panel and revise evidence text**

Start `project.render` directly with the five metrics. Use `REFERENCE ITEMS` for the curated-item count. Render the approved strings exactly:

```python
st.markdown(
    '<div class="lineage-band">2023 COLLEGE STUDENT STUDY -> '
    "2026 ADOLESCENT RECONSTRUCTION -> FUTURE VALIDATION</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-heading">2023 STUDY / COLLEGE STUDENT SAMPLE</div>',
    unsafe_allow_html=True,
)
archived = pd.DataFrame(_ARCHIVED_EVIDENCE, columns=("DOMAIN", "ALPHA", "OMEGA"))
st.dataframe(archived, hide_index=True, use_container_width=True, height=214)
st.markdown(
    '<div class="evidence-note">Historical summary from the 2023 '
    "college-student study; raw response data are no longer available.</div>",
    unsafe_allow_html=True,
)
```

Remove the unused HTML escaping helper and the separate `Openness item-total r` markdown.

- [ ] **Step 5: Adjust CSS without changing the established palette**

Delete `.top-row`, `.top-badges`, `.mode-badge`, `.availability-badge`,
`.project-band`, `.project-meta`, and `.project-boundary`. Change the shared
badge declaration so it targets `.status-badge` alone, then add:

```css
.top-meta {
    border-top: 1px solid #3F3F43;
    color: #D5D5D7;
    display: flex;
    flex-wrap: wrap;
    gap: 6px 18px;
    margin-top: 13px;
    padding-top: 10px;
}
.top-meta span {
    font-size: 13px;
    font-weight: 650;
}
.evidence-note {
    color: var(--muted);
    font-size: 13px;
    margin-top: 10px;
}
```

Remove the obsolete mobile rules for `.top-row` and `.top-badges`.

- [ ] **Step 6: Run the Project/header tests**

Run: `python -m pytest tests/test_app_smoke.py -q -k "starts_without or project_page or project_curated_candidate_metric or review_header"`

Expected: all selected tests pass, with obsolete header-mode tests replaced by badge-absence assertions.

- [ ] **Step 7: Commit the formal Project layout**

```powershell
git add -- app_v2.py psychometric_v2/ui/components.py psychometric_v2/ui/pages/project.py psychometric_v2/ui/theme.py tests/test_app_smoke.py
git commit -m "feat: formalize project overview"
```

### Task 3: Add session-scoped unlocking to Generation Studio

**Files:**
- Modify: `tests/test_app_smoke.py`
- Modify: `psychometric_v2/ui/state.py`
- Modify: `psychometric_v2/ui/pages/generation.py`

- [ ] **Step 1: Add failing locked, rejected, and unlocked UI tests**

```python
def test_generation_studio_is_locked_by_default(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")

    app = _run_app("GENERATION STUDIO")

    assert not app.exception
    assert app.session_state["v2_live_unlocked"] is False
    assert _button(app, "GENERATE").disabled is True
    assert _button(app, "LOAD REFERENCE ITEM").disabled is False
    assert not any(widget.key == "v2_generation_mode" for widget in app.selectbox)


def test_generation_studio_rejects_an_incorrect_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")
    app = _run_app("GENERATION STUDIO")

    _widget_with_key(app.text_input, "v2_live_access_input").set_value("wrong")
    _button(app, "UNLOCK").click().run()

    assert app.session_state["v2_live_unlocked"] is False
    assert [error.value for error in app.error] == ["Access code not recognized."]


def test_generation_studio_unlocks_for_the_current_session(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")
    app = _run_app("GENERATION STUDIO")

    _widget_with_key(app.text_input, "v2_live_access_input").set_value(
        "job-talk-2026"
    )
    _button(app, "UNLOCK").click().run()

    assert app.session_state["v2_live_unlocked"] is True
    assert _button(app, "GENERATE").disabled is False
```

- [ ] **Step 2: Add a failing defense-in-depth test**

Monkeypatch `generation.st.button` so only `GENERATE` returns true even when the rendered button would be disabled. Make `LiveModelConfig.from_env` raise if called. Assert the app reports `Live generation is locked.` and the forbidden initializer is never reached.

```python
def test_forced_generate_cannot_bypass_the_session_lock(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")
    original_button = generation.st.button
    calls = []

    def forced_button(label, *args, **kwargs):
        if label == "GENERATE":
            return True
        return original_button(label, *args, **kwargs)

    def forbidden_config():
        calls.append("config")
        raise AssertionError("locked generation initialized the model")

    monkeypatch.setattr(generation.st, "button", forced_button)
    monkeypatch.setattr(
        generation.LiveModelConfig,
        "from_env",
        staticmethod(forbidden_config),
    )
    app = _run_app("GENERATION STUDIO")

    assert not app.exception
    assert calls == []
    assert "Live generation is locked." in [error.value for error in app.error]
```

- [ ] **Step 3: Run the new tests and confirm the missing controls/state failures**

Run: `python -m pytest tests/test_app_smoke.py -q -k "locked_by_default or incorrect_code or unlocks_for or forced_generate"`

Expected: failures show missing `v2_live_unlocked`, old button text, and absent unlock controls.

- [ ] **Step 4: Initialize session state and add unlock callbacks**

Add to `_DEFAULTS` in `state.py`:

```python
"v2_live_unlocked": False,
"v2_live_access_error": None,
```

In `generation.py`, import the verifier and add:

```python
from psychometric_v2.live_access import (
    live_access_configured,
    verify_live_access_code,
)


def _live_access_granted() -> bool:
    return live_access_configured() and bool(
        st.session_state.get("v2_live_unlocked", False)
    )


def _submit_live_access_code() -> None:
    submitted = str(st.session_state.get("v2_live_access_input", ""))
    if verify_live_access_code(submitted):
        st.session_state["v2_live_unlocked"] = True
        st.session_state["v2_live_access_error"] = None
    else:
        st.session_state["v2_live_unlocked"] = False
        st.session_state["v2_live_access_error"] = "Access code not recognized."
    st.session_state["v2_live_access_input"] = ""
```

- [ ] **Step 5: Replace the mode selector with the access panel**

Use four selection columns for domain, facet, context, and anchor. Read the internal mode from session state instead of exposing a selectbox:

```python
mode = str(
    st.session_state.get(
        "v2_generation_mode",
        GenerationMode.CURATED.value,
    )
)
if mode not in (GenerationMode.CURATED.value, GenerationMode.LIVE.value):
    mode = GenerationMode.CURATED.value
    st.session_state["v2_generation_mode"] = mode
controls = st.columns(4, gap="small")
```

Before the action buttons, render:

```python
access_configured = live_access_configured()
access_granted = _live_access_granted()
if access_granted:
    st.caption("LIVE GENERATION UNLOCKED FOR THIS SESSION")
elif access_configured:
    with st.expander("UNLOCK LIVE GENERATION", expanded=False):
        st.text_input(
            "LIVE ACCESS CODE",
            type="password",
            key="v2_live_access_input",
        )
        st.button(
            "UNLOCK",
            key="v2_unlock_live",
            on_click=_submit_live_access_code,
            use_container_width=True,
        )
else:
    st.info("Live generation access is not configured.")
access_error = st.session_state.get("v2_live_access_error")
if access_error:
    st.error(str(access_error))
```

Set `GENERATE` disabled unless both `_live_environment_present()` and
`access_granted` are true. Rename the reference button to `LOAD REFERENCE ITEM`.

- [ ] **Step 6: Guard the server-side branch before model initialization**

At the beginning of `if generate`, perform the second check:

```python
if generate and not _live_access_granted():
    st.session_state["v2_generation_error"] = "Live generation is locked."
elif generate:
    st.session_state["v2_generation_mode"] = GenerationMode.LIVE.value
    # Existing generation, persistence, and sanitized error-handling block.
```

Keep `_load_curated` as the internal data operation, but have the renamed
reference button call it. Loading a reference item sets the internal mode back
to `GenerationMode.CURATED.value` and never checks the access code.

- [ ] **Step 7: Update existing live tests to authorize their sessions explicitly**

For every existing test that intentionally clicks `GENERATE`, set:

```python
monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")
app.session_state["v2_live_unlocked"] = True
```

Replace `LOAD CURATED EXAMPLE` assertions with `LOAD REFERENCE ITEM`. Remove
header badge assertions and retain internal `GenerationMode.CURATED` assertions
where they test persisted data rather than visible copy.

- [ ] **Step 8: Run all generation and access tests**

Run: `python -m pytest tests/test_live_access.py tests/test_app_smoke.py -q -k "generation or live or access or reference"`

Expected: all selected tests pass and no secret value appears in failure output.

- [ ] **Step 9: Commit the protected Generation Studio**

```powershell
git add -- psychometric_v2/ui/state.py psychometric_v2/ui/pages/generation.py tests/test_app_smoke.py
git commit -m "feat: protect live generation with session access"
```

### Task 4: Verify the complete release locally

**Files:**
- Verify: all tracked files

- [ ] **Step 1: Run whitespace and secret scans**

Run:

```powershell
git diff --check origin/master...HEAD
git grep -n -I -E 'sk-[A-Za-z0-9_-]{20,}' HEAD
```

Expected: no whitespace errors and no tracked API-key match.

- [ ] **Step 2: Run the complete automated suite**

Run: `python -m pytest -ra`

Expected: all tests pass; the existing Windows symlink-permission test may remain skipped.

- [ ] **Step 3: Start or reload the local Streamlit app**

Run: `python -m streamlit run app_v2.py --server.port 8502`

Expected: the application is available at `http://localhost:8502/`.

- [ ] **Step 4: Browser-test desktop and mobile layouts**

At desktop and mobile widths, verify:

- Project has one black identity panel and no repeated title block.
- Project metadata wraps without overlap.
- The 2023 college-student lineage, revised metric, and quiet footnote render.
- `CURATED DEMO`, `LIVE AVAILABLE`, and `LIVE UNAVAILABLE` are absent.
- Generation Studio opens with the reference item, keeps `GENERATE` disabled,
  rejects a wrong code, and unlocks only for the current session.
- Construct Map remains visually unchanged.

- [ ] **Step 5: Re-run the full suite after browser verification**

Run: `python -m pytest -ra`

Expected: all tests still pass. If browser verification found a defect, add a
failing AppTest assertion before correcting it, commit only the named test and
implementation files, and repeat this command.

### Task 5: Publish and update Streamlit Secrets

**Files:**
- Deploy from: `app_v2.py`
- Branch: `master`

- [ ] **Step 1: Push the feature branch and open a PR**

```powershell
git push -u origin codex/formal-release-live-access
gh pr create --base master --head codex/formal-release-live-access --title "Formalize workbench and protect live generation" --body "## Summary`n- consolidate the formal Project overview`n- protect live generation with session access`n- retain public reference-item browsing`n`n## Test plan`n- python -m pytest -ra`n- desktop and mobile Streamlit verification"
```

Expected: GitHub reports a mergeable PR targeting `master`.

- [ ] **Step 2: Review and merge the PR with a normal merge commit**

Run: `gh pr merge codex/formal-release-live-access --repo YaoZeLiu0417/LLM_Psychometric --merge`

Expected: the PR state becomes `MERGED`; do not delete the feature branch until deployment is verified.

- [ ] **Step 3: Add `LIVE_ACCESS_CODE` to Streamlit Secrets**

Ask the operator to add `LIVE_ACCESS_CODE` to the ignored local `.env` and to
confirm when it is present. Read that value without emitting it, preserve the
three existing root-level model secrets, and enter the fourth root-level key
directly in Streamlit Community Cloud. The real value must not appear in Git,
terminal output, tests, screenshots, or conversation text.

- [ ] **Step 4: Wait for automatic deployment and verify the locked public state**

Open `https://adolescent-big-five-workbench.streamlit.app/` in an unauthenticated
session. Confirm public research pages load, `GENERATE` remains disabled, and a
forced or incorrect access attempt does not initialize the model.

- [ ] **Step 5: Verify the authorized state without triggering a paid generation**

Enter the production access code, confirm `GENERATE` becomes enabled for that
session, then end the session. Reopen the app and confirm it is locked again.
Do not click `GENERATE` during deployment verification.

- [ ] **Step 6: Record final evidence**

Report the merged PR URL, deployed URL, full pytest result, desktop/mobile visual
checks, locked and unlocked access results, and the fact that no paid model call
was made.
