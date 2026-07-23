# Participant Pilot Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show promoted pilot candidates in Participant View and use curated references only when no pilot candidates exist.

**Architecture:** Keep Participant View's rendering and response flow unchanged. Replace the current CURATED-only slice in `_preview_items()` with a two-tier selector: all `PILOT_CANDIDATE` items first, otherwise the first five curated items.

**Tech Stack:** Python 3.12, Streamlit 1.60, Pydantic models, pytest, Streamlit AppTest

---

### Task 1: Select participant-ready pilot candidates

**Files:**
- Modify: `psychometric_v2/ui/pages/participant.py:5-25`
- Test: `tests/test_app_smoke.py:518-635`

- [ ] **Step 1: Write the failing participant-pool regression test**

Add an AppTest that builds a project containing curated seeds, one `LIVE` item with `HUMAN_REVIEWED`, and one `LIVE` item with `PILOT_CANDIDATE`. Give the pilot item a unique stem, render Participant View, and assert:

```python
assert "PILOT ITEM VISIBLE TO PARTICIPANTS" in markdown
assert "HUMAN REVIEWED ITEM MUST STAY HIDDEN" not in markdown
assert "1 / 1" in markdown
```

The test fixture must use valid `GenerationMetadata` for both live items and set `EvidenceStatus` explicitly.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m pytest tests/test_app_smoke.py -k "participant_prefers_pilot" -q
```

Expected: FAIL because the current `_preview_items()` returns only curated items.

- [ ] **Step 3: Implement the minimal two-tier selector**

Import `EvidenceStatus` and implement:

```python
def _preview_items(project: ResearchProject) -> tuple[CandidateItem, ...]:
    pilot_candidates = tuple(
        item
        for item in project.items.values()
        if item.evidence_status is EvidenceStatus.PILOT_CANDIDATE
    )
    if pilot_candidates:
        return pilot_candidates
    return tuple(
        item
        for item in project.items.values()
        if item.generation_mode is GenerationMode.CURATED
    )[:5]
```

- [ ] **Step 4: Run focused participant tests and verify GREEN**

Run:

```powershell
python -m pytest tests/test_app_smoke.py -k "participant" -q
```

Expected: all selected participant tests pass.

- [ ] **Step 5: Run the full suite**

Run:

```powershell
python -m pytest -q
```

Expected: exit code 0 with only the existing expected skip.

- [ ] **Step 6: Commit the implementation**

```powershell
git add psychometric_v2/ui/pages/participant.py tests/test_app_smoke.py
git commit -m "fix: show pilot candidates in participant preview"
```

