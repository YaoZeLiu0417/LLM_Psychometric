# Public Demo Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Streamlit workbench anonymously browsable while protecting every model-backed or research-record mutation behind session-scoped Researcher Access and isolating public-demo data per visitor.

**Architecture:** Add fail-closed deployment settings and a Streamlit-session runtime that owns a temporary JSON repository in `public_demo` mode while preserving the durable repository in explicit `research` mode. Move Researcher Access into a shared pure controller, inject the resulting authorization into `WorkbenchService`, and enforce a three-start generation budget before any model client is constructed. Release automation scans both the checked-out tree and every reachable Git blob before repository visibility changes.

**Tech Stack:** Python 3.11+, Streamlit, Pydantic 2, pytest, Streamlit AppTest, Git plumbing

---

## File Structure

- Create `psychometric_v2/deployment.py`: validated deployment mode and generation-limit configuration.
- Create `psychometric_v2/session_runtime.py`: session repository lifetime, Researcher Access state, and generation budget.
- Modify `psychometric_v2/live_access.py`: retain constant-time code verification and expose session-state grant helpers without importing Streamlit.
- Modify `psychometric_v2/workbench.py`: enforce injected mutation authorization at the service boundary.
- Modify `psychometric_v2/ui/state.py`: initialize only non-secret session keys needed by access and generation accounting.
- Create `psychometric_v2/ui/researcher_access.py`: one shared Researcher Access control rendered on Generation and Review.
- Modify `psychometric_v2/ui/pages/generation.py`: use shared access, enforce budget before model construction, and preserve reference loading.
- Modify `psychometric_v2/ui/pages/review.py`: keep review content visible but disable editing and actions until authorized.
- Modify `app_v2.py`: build deployment settings, repository, and authorized service from session state.
- Create `scripts/audit_public_release.py`: scan tracked worktree files and every reachable Git blob for secret and personal-path patterns.
- Create `tests/test_deployment.py`, `tests/test_session_runtime.py`, and `tests/test_public_release_audit.py`; extend existing access, workbench, app smoke, environment, and README tests.
- Modify `.env.example`, `.gitignore`, `README.md`, and `README_V2.md`: document deployment modes, isolation, access boundaries, and public release procedure.

### Task 1: Deployment Configuration

**Files:**
- Create: `psychometric_v2/deployment.py`
- Create: `tests/test_deployment.py`
- Modify: `.env.example`

- [ ] **Step 1: Write failing tests for the safe default, explicit research mode, configured public limit, and invalid values**

```python
import pytest

from psychometric_v2.deployment import DeploymentMode, DeploymentSettings


def test_deployment_defaults_to_public_demo(monkeypatch) -> None:
    monkeypatch.delenv("WORKBENCH_DEPLOYMENT", raising=False)
    monkeypatch.delenv("PUBLIC_DEMO_GENERATION_LIMIT", raising=False)

    settings = DeploymentSettings.from_env()

    assert settings.mode is DeploymentMode.PUBLIC_DEMO
    assert settings.public_demo_generation_limit == 3


def test_deployment_accepts_explicit_research_mode(monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_DEPLOYMENT", "research")

    assert DeploymentSettings.from_env().mode is DeploymentMode.RESEARCH


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("WORKBENCH_DEPLOYMENT", "production"),
        ("PUBLIC_DEMO_GENERATION_LIMIT", "0"),
        ("PUBLIC_DEMO_GENERATION_LIMIT", "four"),
    ),
)
def test_deployment_rejects_invalid_values(monkeypatch, name: str, value: str) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="deployment configuration"):
        DeploymentSettings.from_env()
```

- [ ] **Step 2: Run the focused tests and verify they fail because the module does not exist**

Run: `python -m pytest tests/test_deployment.py -q`

Expected: FAIL during collection with `ModuleNotFoundError: psychometric_v2.deployment`.

- [ ] **Step 3: Implement frozen settings with a fail-closed public-demo default**

```python
from __future__ import annotations

import os
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class DeploymentMode(str, Enum):
    RESEARCH = "research"
    PUBLIC_DEMO = "public_demo"


class DeploymentSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: DeploymentMode = DeploymentMode.PUBLIC_DEMO
    public_demo_generation_limit: int = Field(default=3, ge=1)

    @classmethod
    def from_env(cls) -> "DeploymentSettings":
        raw_mode = os.getenv("WORKBENCH_DEPLOYMENT", "").strip() or "public_demo"
        raw_limit = os.getenv("PUBLIC_DEMO_GENERATION_LIMIT", "").strip() or "3"
        try:
            return cls(
                mode=raw_mode,
                public_demo_generation_limit=int(raw_limit),
            )
        except (TypeError, ValueError, ValidationError):
            raise ValueError("Invalid workbench deployment configuration.") from None
```

Add these non-secret defaults to `.env.example`:

```dotenv
WORKBENCH_DEPLOYMENT=research
PUBLIC_DEMO_GENERATION_LIMIT=3
```

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `python -m pytest tests/test_deployment.py -q`

Expected: `5 passed`.

- [ ] **Step 5: Commit the deployment configuration**

```powershell
git add psychometric_v2/deployment.py tests/test_deployment.py .env.example
git commit -m "feat: add safe deployment settings"
```

### Task 2: Session-Scoped Public Repository

**Files:**
- Create: `psychometric_v2/session_runtime.py`
- Create: `tests/test_session_runtime.py`
- Modify: `psychometric_v2/ui/state.py`

- [ ] **Step 1: Write failing tests for public-session isolation, rerun reuse, research persistence, and generation starts**

```python
from pathlib import Path

import pytest

from psychometric_v2.deployment import DeploymentMode, DeploymentSettings
from psychometric_v2.session_runtime import (
    GenerationLimitReached,
    generation_attempts,
    repository_for_session,
    start_generation,
)


def settings(mode: DeploymentMode) -> DeploymentSettings:
    return DeploymentSettings(mode=mode, public_demo_generation_limit=3)


def test_public_demo_repository_reuses_one_session_and_isolates_another(tmp_path) -> None:
    first: dict[str, object] = {}
    second: dict[str, object] = {}

    first_repository = repository_for_session(first, settings(DeploymentMode.PUBLIC_DEMO), tmp_path)
    rerun_repository = repository_for_session(first, settings(DeploymentMode.PUBLIC_DEMO), tmp_path)
    second_repository = repository_for_session(second, settings(DeploymentMode.PUBLIC_DEMO), tmp_path)

    assert first_repository.root == rerun_repository.root
    assert first_repository.root != second_repository.root
    assert first_repository.root not in (tmp_path / "v2" / "projects").parents


def test_research_repository_uses_durable_workspace(tmp_path) -> None:
    repository = repository_for_session({}, settings(DeploymentMode.RESEARCH), tmp_path)

    assert repository.root == (tmp_path / "v2" / "projects").resolve()


def test_generation_budget_counts_starts_and_blocks_fourth() -> None:
    state: dict[str, object] = {}
    configured = settings(DeploymentMode.PUBLIC_DEMO)

    for expected in (1, 2, 3):
        start_generation(state, configured)
        assert generation_attempts(state) == expected

    with pytest.raises(GenerationLimitReached):
        start_generation(state, configured)
    assert generation_attempts(state) == 3
```

- [ ] **Step 2: Run the tests and verify the missing runtime module fails collection**

Run: `python -m pytest tests/test_session_runtime.py -q`

Expected: FAIL with `ModuleNotFoundError: psychometric_v2.session_runtime`.

- [ ] **Step 3: Implement repository lifetime and generation accounting**

```python
from __future__ import annotations

import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.deployment import DeploymentMode, DeploymentSettings
from psychometric_v2.repository import JsonProjectRepository


_TEMP_DIRECTORY_KEY = "v2_public_demo_temp_directory"
_REPOSITORY_ROOT_KEY = "v2_public_demo_repository_root"
_GENERATION_ATTEMPTS_KEY = "v2_generation_attempts"


class GenerationLimitReached(PermissionError):
    pass


def repository_for_session(
    state: MutableMapping[str, Any],
    settings: DeploymentSettings,
    workspace_root: Path,
) -> JsonProjectRepository:
    if settings.mode is DeploymentMode.RESEARCH:
        repository = JsonProjectRepository(workspace_root / "v2" / "projects")
        repository.ensure_seed(build_demo_project())
        return repository

    temporary = state.get(_TEMP_DIRECTORY_KEY)
    root_text = state.get(_REPOSITORY_ROOT_KEY)
    if not isinstance(temporary, tempfile.TemporaryDirectory) or not isinstance(root_text, str):
        temporary = tempfile.TemporaryDirectory(prefix="psychometric-public-demo-")
        root = Path(temporary.name) / "projects"
        state[_TEMP_DIRECTORY_KEY] = temporary
        state[_REPOSITORY_ROOT_KEY] = str(root)
    else:
        root = Path(root_text)
    repository = JsonProjectRepository(root)
    repository.ensure_seed(build_demo_project())
    return repository


def generation_attempts(state: MutableMapping[str, Any]) -> int:
    value = state.get(_GENERATION_ATTEMPTS_KEY, 0)
    return value if isinstance(value, int) and value >= 0 else 0


def generation_remaining(
    state: MutableMapping[str, Any],
    settings: DeploymentSettings,
) -> int | None:
    if settings.mode is DeploymentMode.RESEARCH:
        return None
    return max(settings.public_demo_generation_limit - generation_attempts(state), 0)


def start_generation(
    state: MutableMapping[str, Any],
    settings: DeploymentSettings,
) -> None:
    remaining = generation_remaining(state, settings)
    if remaining is not None and remaining <= 0:
        raise GenerationLimitReached("Generation limit reached for this session.")
    state[_GENERATION_ATTEMPTS_KEY] = generation_attempts(state) + 1
```

Add `"v2_generation_attempts": 0` to `_DEFAULTS` in `psychometric_v2/ui/state.py`. Do not put a `TemporaryDirectory` into `_DEFAULTS`; it must be created lazily for each real Streamlit session.

- [ ] **Step 4: Run focused repository and runtime tests**

Run: `python -m pytest tests/test_session_runtime.py tests/test_repository.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit the session runtime**

```powershell
git add psychometric_v2/session_runtime.py psychometric_v2/ui/state.py tests/test_session_runtime.py
git commit -m "feat: isolate public demo sessions"
```

### Task 3: Shared Researcher Access and Service Authorization

**Files:**
- Modify: `psychometric_v2/live_access.py`
- Modify: `psychometric_v2/workbench.py`
- Modify: `tests/test_live_access.py`
- Modify: `tests/test_workbench.py`

- [ ] **Step 1: Write failing tests for grant lifecycle and service-level denial**

Append to `tests/test_live_access.py`:

```python
from psychometric_v2.live_access import (
    clear_researcher_access,
    researcher_access_granted,
    submit_researcher_access_code,
)


def test_researcher_access_grant_stores_no_plaintext_and_rotates(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-a")
    state: dict[str, object] = {"v2_researcher_access_input": "test-only-access-a"}

    assert submit_researcher_access_code(state) is True
    assert researcher_access_granted(state) is True
    assert state["v2_researcher_access_input"] == ""
    assert "test-only-access-a" not in repr(state)

    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-b")
    assert researcher_access_granted(state) is False


def test_researcher_access_rejects_and_clears_input(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-a")
    state: dict[str, object] = {"v2_researcher_access_input": "wrong"}

    assert submit_researcher_access_code(state) is False
    assert state["v2_researcher_access_input"] == ""
    assert researcher_access_granted(state) is False
```

Append to `tests/test_workbench.py`:

```python
from psychometric_v2.workbench import MutationPermissionError


def test_unauthorized_service_denies_review_and_generation_without_writes(tmp_path) -> None:
    service, repository, project = service_with_seed(tmp_path)
    service = WorkbenchService(repository, mutation_authorized=False)
    item = next(iter(project.items.values()))

    with pytest.raises(MutationPermissionError):
        review(service, project.config.project_id, item)
    with pytest.raises(MutationPermissionError):
        service.save_generated_item(project.config.project_id, item)

    assert repository.load(project.config.project_id) == project
```

- [ ] **Step 2: Run focused tests and verify missing functions/signatures fail**

Run: `python -m pytest tests/test_live_access.py tests/test_workbench.py -q`

Expected: FAIL for missing session helpers, `MutationPermissionError`, and constructor argument.

- [ ] **Step 3: Implement access state helpers and service guard**

In `psychometric_v2/live_access.py`, add:

```python
from collections.abc import MutableMapping
from typing import Any

_UNLOCKED_KEY = "v2_researcher_unlocked"
_FINGERPRINT_KEY_STATE = "v2_researcher_access_fingerprint"
_INPUT_KEY = "v2_researcher_access_input"
_ERROR_KEY = "v2_researcher_access_error"


def clear_researcher_access(state: MutableMapping[str, Any]) -> None:
    state[_UNLOCKED_KEY] = False
    state[_FINGERPRINT_KEY_STATE] = None


def researcher_access_granted(state: MutableMapping[str, Any]) -> bool:
    current = live_access_fingerprint()
    stored = state.get(_FINGERPRINT_KEY_STATE)
    if (
        current is None
        or state.get(_UNLOCKED_KEY) is not True
        or not isinstance(stored, str)
        or not hmac.compare_digest(stored, current)
    ):
        clear_researcher_access(state)
        return False
    return True


def submit_researcher_access_code(state: MutableMapping[str, Any]) -> bool:
    submitted = str(state.get(_INPUT_KEY, ""))
    fingerprint = live_access_fingerprint()
    accepted = fingerprint is not None and verify_live_access_code(submitted)
    state[_INPUT_KEY] = ""
    if accepted:
        state[_UNLOCKED_KEY] = True
        state[_FINGERPRINT_KEY_STATE] = fingerprint
        state[_ERROR_KEY] = None
    else:
        clear_researcher_access(state)
        state[_ERROR_KEY] = "Access code not recognized."
    return accepted
```

In `psychometric_v2/workbench.py`, add the dedicated error and constructor guard:

```python
class MutationPermissionError(PermissionError):
    pass


class WorkbenchService:
    def __init__(self, repository: Any, *, mutation_authorized: bool = True) -> None:
        self.repository = repository
        self.mutation_authorized = mutation_authorized

    def _require_mutation_authorized(self) -> None:
        if not self.mutation_authorized:
            raise MutationPermissionError("Researcher Access is required.")
```

Call `self._require_mutation_authorized()` as the first statement of both `review_item` and `save_generated_item`, before validation, loading, or locking.

- [ ] **Step 4: Run focused access and service tests**

Run: `python -m pytest tests/test_live_access.py tests/test_workbench.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit authorization enforcement**

```powershell
git add psychometric_v2/live_access.py psychometric_v2/workbench.py tests/test_live_access.py tests/test_workbench.py
git commit -m "feat: enforce researcher mutations"
```

### Task 4: Shared Researcher Access UI and Application Wiring

**Files:**
- Create: `psychometric_v2/ui/researcher_access.py`
- Modify: `psychometric_v2/ui/state.py`
- Modify: `app_v2.py`
- Modify: `tests/test_app_smoke.py`

- [ ] **Step 1: Write failing smoke tests for the public default and shared unlock**

Add helpers in `tests/test_app_smoke.py` to clear deployment variables alongside existing model-variable cleanup, then add:

```python
def test_public_demo_default_uses_session_repository(monkeypatch) -> None:
    monkeypatch.delenv("WORKBENCH_DEPLOYMENT", raising=False)
    app = _run_app("PROJECT")

    assert not app.exception
    assert "v2_public_demo_repository_root" in app.session_state
    assert "workspace_data" not in app.session_state["v2_public_demo_repository_root"]


def test_one_researcher_unlock_is_shared_by_generation_and_review(monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_DEPLOYMENT", "public_demo")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-model-key")
    monkeypatch.setenv("LLM_MODEL", "fake-model")
    app = _run_app("GENERATION STUDIO")

    app.text_input(key="v2_researcher_access_input").set_value("test-only-access")
    _button(app, "UNLOCK").click().run()
    app.get("button_group")[0].set_value(["REVIEW"]).run()

    assert not app.exception
    assert app.text_area(key="v2_review_stem_" + app.session_state["v2_review_item"]).disabled is False
    assert _button(app, "APPROVE CONTENT").disabled is False
```

- [ ] **Step 2: Run the new smoke tests and verify they fail**

Run: `python -m pytest tests/test_app_smoke.py -k "public_demo_default or one_researcher_unlock" -q`

Expected: FAIL because app wiring and shared access UI do not exist.

- [ ] **Step 3: Create the shared UI control**

```python
from __future__ import annotations

import streamlit as st

from psychometric_v2.live_access import (
    live_access_configured,
    researcher_access_granted,
    submit_researcher_access_code,
)


def render_researcher_access() -> bool:
    granted = researcher_access_granted(st.session_state)
    if granted:
        st.caption("RESEARCHER ACCESS ENABLED FOR THIS SESSION")
    elif live_access_configured():
        with st.expander("RESEARCHER ACCESS"):
            st.text_input(
                "ACCESS CODE",
                type="password",
                key="v2_researcher_access_input",
            )
            st.button(
                "UNLOCK",
                key="v2_unlock_researcher",
                on_click=submit_researcher_access_code,
                args=(st.session_state,),
            )
    else:
        st.info("Researcher Access is not configured; this session is read-only.")

    error = st.session_state.get("v2_researcher_access_error")
    if error:
        st.error(str(error))
    return granted
```

Initialize `v2_researcher_unlocked`, `v2_researcher_access_fingerprint`, and `v2_researcher_access_error` in `ui/state.py`; do not initialize or persist a raw code.

- [ ] **Step 4: Wire settings, session repository, and authorized service in `app_v2.py`**

Replace the fixed repository construction with:

```python
from psychometric_v2.deployment import DeploymentMode, DeploymentSettings
from psychometric_v2.live_access import researcher_access_granted
from psychometric_v2.session_runtime import repository_for_session

try:
    deployment = DeploymentSettings.from_env()
except ValueError:
    st.error("Workbench deployment configuration is invalid.")
    st.stop()

try:
    repository = repository_for_session(
        st.session_state,
        deployment,
        WORKSPACE_ROOT,
    )
except OSError:
    st.error("This workbench session is temporarily unavailable.")
    st.stop()

research_project = repository.load("adolescent-big-five-demo")
mutation_authorized = (
    deployment.mode is DeploymentMode.RESEARCH
    or researcher_access_granted(st.session_state)
)
workbench = WorkbenchService(
    repository,
    mutation_authorized=mutation_authorized,
)
```

Pass `deployment` as the fourth positional argument only to `generation.render`; keep the other renderer signatures stable by branching explicitly rather than changing all pages:

```python
if active_page == "GENERATION STUDIO":
    generation.render(research_project, construct_anchors, workbench, deployment)
else:
    page_renderers[active_page](research_project, construct_anchors, workbench)
```

- [ ] **Step 5: Run app-start and shared-access smoke tests**

Run: `python -m pytest tests/test_app_smoke.py -k "starts_without or public_demo_default or one_researcher_unlock" -q`

Expected: all selected tests pass after Tasks 5 and 6 finish their page changes; at this checkpoint, only app-start and repository assertions must pass.

- [ ] **Step 6: Commit runtime wiring**

```powershell
git add app_v2.py psychometric_v2/ui/researcher_access.py psychometric_v2/ui/state.py tests/test_app_smoke.py
git commit -m "feat: wire public demo runtime"
```

### Task 5: Generation Access and Session Budget

**Files:**
- Modify: `psychometric_v2/ui/pages/generation.py`
- Modify: `tests/test_app_smoke.py`

- [ ] **Step 1: Replace old live-access smoke expectations and add no-client/budget tests**

Use `v2_researcher_access_input` in the existing access tests. Add a fake client constructor counter and assert all locked paths leave it at zero:

```python
def test_anonymous_forced_generate_never_constructs_model_client(monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_DEPLOYMENT", "public_demo")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-model-key")
    monkeypatch.setenv("LLM_MODEL", "fake-model")
    constructed = 0

    class ForbiddenClient:
        def __init__(self, config) -> None:
            nonlocal constructed
            constructed += 1

    monkeypatch.setattr(generation, "OpenAICompatibleClient", ForbiddenClient)
    app = _run_app("GENERATION STUDIO")
    app.session_state["v2_generate"] = True
    app.run()

    assert not app.exception
    assert constructed == 0
    assert app.session_state["v2_generation_attempts"] == 0
```

Add a successful fake pipeline and run three starts, then force a fourth event:

```python
def test_public_demo_fourth_generation_is_blocked_before_client(monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_DEPLOYMENT", "public_demo")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-model-key")
    monkeypatch.setenv("LLM_MODEL", "fake-model")
    constructed = 0

    class ForbiddenClient:
        def __init__(self, config) -> None:
            nonlocal constructed
            constructed += 1

    _force_generate_event(monkeypatch)
    monkeypatch.setattr(generation, "OpenAICompatibleClient", ForbiddenClient)
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    app.session_state["v2_active_page"] = "GENERATION STUDIO"
    app.session_state["v2_generation_attempts"] = 3
    _authorize_researcher_session(app)
    app.run()

    assert not app.exception
    assert constructed == 0
    assert app.session_state["v2_generation_attempts"] == 3
    assert "generation limit" in _markdown(app).lower()
```

The pure runtime test in Task 2 proves that starts one through three increment exactly once. This AppTest proves that an exhausted fourth event cannot reach model construction.

- [ ] **Step 2: Run generation access tests and verify the new budget behavior fails**

Run: `python -m pytest tests/test_app_smoke.py -k "live_access or anonymous_forced or fourth_generation or live_success or live_failure" -q`

Expected: new tests fail because the legacy page-local access functions and unlimited generation path remain.

- [ ] **Step 3: Replace page-local access logic and increment before client construction**

Change the signature and access block:

```python
from psychometric_v2.deployment import DeploymentSettings
from psychometric_v2.session_runtime import (
    GenerationLimitReached,
    generation_remaining,
    start_generation,
)
from psychometric_v2.ui.researcher_access import render_researcher_access


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
    deployment: DeploymentSettings,
) -> None:
    researcher_access = render_researcher_access()
    remaining = generation_remaining(st.session_state, deployment)
    budget_available = remaining is None or remaining > 0
```

Render `GENERATE` with `disabled=not live_ready or not researcher_access or not budget_available`. Show `PUBLIC DEMO GENERATIONS REMAINING: {remaining}` when `remaining is not None`.

At the start of the forced-event-safe generation branch:

```python
if generate:
    if not researcher_access_granted(st.session_state):
        st.session_state["v2_generation_error"] = "Researcher Access is required."
    else:
        try:
            start_generation(st.session_state, deployment)
        except GenerationLimitReached:
            st.session_state["v2_generation_error"] = (
                "The generation limit for this session has been reached."
            )
        else:
            try:
                config = LiveModelConfig.from_env()
                client = OpenAICompatibleClient(config)
                pipeline = GenerationPipeline(client)
                generated = pipeline.generate_candidate(
                    project.config,
                    anchors[anchor_id],
                    context_domain,
                )
```

Keep `start_generation` immediately before `LiveModelConfig.from_env()`; thus missing/invalid model configuration after an authorized start is still counted, while anonymous and exhausted events never construct a client.

- [ ] **Step 4: Run the complete generation smoke subset**

Run: `python -m pytest tests/test_app_smoke.py -k "generation or live_access or live_success or live_failure or reference_loading" -q`

Expected: all selected tests pass, including legacy partial-result and persistence behavior.

- [ ] **Step 5: Commit protected generation**

```powershell
git add psychometric_v2/ui/pages/generation.py tests/test_app_smoke.py
git commit -m "feat: limit protected generation"
```

### Task 6: Read-Only Review UI

**Files:**
- Modify: `psychometric_v2/ui/pages/review.py`
- Modify: `tests/test_app_smoke.py`

- [ ] **Step 1: Write failing tests for locked visibility, disabled fields/actions, public downloads, and unlock**

```python
def test_anonymous_review_is_visible_read_only_and_exports_work(monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_DEPLOYMENT", "public_demo")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access")
    app = _run_app("REVIEW")

    assert not app.exception
    assert len(app.dataframe[0].value) == 5
    assert app.text_area[0].disabled is True
    assert all(field.disabled for field in app.text_input if field.key != "v2_researcher_access_input")
    for label in ("SAVE REVISION", "RETURN", "APPROVE CONTENT", "PROMOTE TO PILOT"):
        assert _button(app, label).disabled is True
    assert len(app.get("download_button")) == 2


def test_forced_review_event_cannot_bypass_service_gate(monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_DEPLOYMENT", "public_demo")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access")
    app = _run_app("REVIEW")
    root = Path(app.session_state["v2_public_demo_repository_root"])
    repository = JsonProjectRepository(root)
    project_id = "adolescent-big-five-demo"
    item_id = app.session_state["v2_review_item"]
    original = repository.load(project_id).items[item_id]

    real_button = review.st.button

    def forced_review(label, *args, **kwargs):
        if label == "SAVE REVISION":
            return True
        return real_button(label, *args, **kwargs)

    monkeypatch.setattr(review.st, "button", forced_review)
    app.session_state["v2_review_edit"] = True
    app.run()

    assert not app.exception
    assert "Researcher Access" in _markdown(app)
    assert repository.load(project_id).items[item_id] == original
```

- [ ] **Step 2: Run review lock tests and verify they fail**

Run: `python -m pytest tests/test_app_smoke.py -k "anonymous_review or forced_review or one_researcher_unlock" -q`

Expected: FAIL because the existing Review editor is writable and has no shared access control.

- [ ] **Step 3: Render the shared access control and disable all mutation widgets**

At the start of `review.render`:

```python
from psychometric_v2.live_access import researcher_access_granted
from psychometric_v2.ui.researcher_access import render_researcher_access
from psychometric_v2.workbench import MutationPermissionError

researcher_access = render_researcher_access()
```

Set `disabled=not researcher_access` on the stem, every option, reviewer, and note input. Combine the access flag with existing action conditions:

```python
locked = not researcher_access_granted(st.session_state)
action_specs = (
    ("SAVE REVISION", ReviewAction.EDIT, locked or conflicted),
    ("RETURN", ReviewAction.RETURN, locked or conflicted),
    ("APPROVE CONTENT", ReviewAction.APPROVE, locked or conflicted),
    (
        "PROMOTE TO PILOT",
        ReviewAction.PROMOTE_TO_PILOT,
        locked or conflicted
        or item.evidence_status is not EvidenceStatus.HUMAN_REVIEWED,
    ),
)
```

Recheck `researcher_access_granted(st.session_state)` inside `if action_clicked is not None` before assembling snapshots. Catch `MutationPermissionError` separately and show `"Researcher Access is required to modify review records."` This protects forced Streamlit events and code rotation between render and click.

- [ ] **Step 4: Run all Review and shared-access smoke tests**

Run: `python -m pytest tests/test_app_smoke.py -k "review or one_researcher_unlock or research_download" -q`

Expected: all selected tests pass; reference JSON/CSV downloads remain enabled.

- [ ] **Step 5: Commit read-only Review**

```powershell
git add psychometric_v2/ui/pages/review.py tests/test_app_smoke.py
git commit -m "feat: lock review mutations"
```

### Task 7: Deployment Documentation and Ignore Contract

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `README_V2.md`
- Modify: `tests/test_environment.py`
- Modify: `tests/test_readme.py`

- [ ] **Step 1: Write failing documentation and ignored-secret tests**

Append to `tests/test_environment.py`:

```python
def test_secret_and_generated_paths_are_ignored() -> None:
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", ".streamlit/secrets.toml", "workspace_data/", "*.log"):
        assert pattern in ignored
```

Extend `test_root_readme_documents_the_real_operating_contract` with:

```python
for phrase in (
    "WORKBENCH_DEPLOYMENT",
    "public_demo",
    "research",
    "three generation attempts per session",
    "Researcher Access",
    "session-isolated",
    "anonymous browsing does not consume model tokens",
):
    assert phrase in documentation
```

- [ ] **Step 2: Run environment and README tests and verify the new contract fails**

Run: `python -m pytest tests/test_environment.py tests/test_readme.py -q`

Expected: FAIL on missing public-demo deployment documentation and any absent ignore patterns.

- [ ] **Step 3: Update ignore rules and both operating guides**

Ensure `.gitignore` contains exact rules:

```gitignore
.env
.streamlit/secrets.toml
workspace_data/
*.log
```

Document:

- `WORKBENCH_DEPLOYMENT=research` for durable local/private use.
- Safe default `public_demo`, temporary session repository, and restart non-persistence.
- Anonymous page navigation, Participant View, and reference-only exports make zero model calls.
- Researcher Access protects Generate, edits, Return, Approve, and Promote.
- Public sessions allow three generation starts; failed starts count.
- The provider-capped demo key, model configuration, and access code exist only in Streamlit Secrets.
- The app is not a validated or diagnostic assessment.

Do not add an open-source license or imply public visibility grants reuse rights.

- [ ] **Step 4: Run documentation tests**

Run: `python -m pytest tests/test_environment.py tests/test_readme.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit documentation**

```powershell
git add .gitignore README.md README_V2.md tests/test_environment.py tests/test_readme.py
git commit -m "docs: explain public demo access"
```

### Task 8: Reachable-History Security Audit

**Files:**
- Create: `scripts/audit_public_release.py`
- Create: `tests/test_public_release_audit.py`

- [ ] **Step 1: Write failing scanner tests for clean blobs, credentials, secret assignments, personal paths, and binary skipping**

```python
from scripts.audit_public_release import Finding, scan_content


def test_scan_content_accepts_documented_placeholders() -> None:
    assert scan_content(
        ".env.example",
        b"OPENAI_API_KEY=your-key\nLIVE_ACCESS_CODE=choose-a-strong-code\n",
    ) == ()


def test_scan_content_flags_secret_values_and_personal_paths() -> None:
    findings = scan_content(
        "historical.txt",
        (
            b"OPENAI_API_KEY=sk-" + b"x" * 32
            + b"\nLIVE_ACCESS_CODE=real-secret-value"
            + b"\nC:\\Users\\private-user\\Desktop\\notes.txt"
        ),
    )

    assert {finding.rule for finding in findings} == {
        "credential-shape",
        "nonempty-secret-assignment",
        "personal-path",
    }


def test_scan_content_skips_binary_payloads() -> None:
    assert scan_content("font.ttf", b"\x00\x01\x02sk-" + b"x" * 40) == ()
```

Add an integration test that initializes a temporary Git repository, commits one clean file, then commits and deletes a secret-bearing file; invoke the script with `--repo` and assert the reachable deleted blob still causes a nonzero result.

- [ ] **Step 2: Run scanner tests and verify module import fails**

Run: `python -m pytest tests/test_public_release_audit.py -q`

Expected: FAIL with `ModuleNotFoundError: scripts.audit_public_release`.

- [ ] **Step 3: Implement deterministic tree and reachable-blob scanning**

The script must:

1. Run `git rev-parse --show-toplevel`.
2. Enumerate current tracked paths with `git ls-files -z`.
3. Enumerate reachable objects with `git rev-list --objects --all`.
4. Resolve object types with `git cat-file --batch-check` and scan only blobs.
5. Read blob bytes with `git cat-file blob <oid>`.
6. Skip payloads containing NUL bytes or larger than 5 MiB.
7. Apply compiled byte patterns for credential shapes, non-placeholder secret assignments, Windows/Unix personal paths, and secret filenames.
8. Print only rule, Git object/path identity, and a redacted description; never print matched secret text.
9. Exit `1` when findings exist, `0` when clean, and `2` for Git/runtime errors.

Use this public interface so unit tests remain independent of subprocess output:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    rule: str
    source: str
    description: str


def scan_content(source: str, content: bytes) -> tuple[Finding, ...]:
    ...


def audit_repository(repo: Path) -> tuple[Finding, ...]:
    ...


def main(argv: list[str] | None = None) -> int:
    ...
```

Placeholder assignments in `.env.example` such as `your-key`, `model-name`, `optional-compatible-endpoint`, and `choose-a-strong-code` must not be findings. Deduplicate identical `(rule, object-id, path)` results.

- [ ] **Step 4: Run scanner unit and integration tests**

Run: `python -m pytest tests/test_public_release_audit.py -q`

Expected: all tests pass, including detection of a secret deleted from the checked-out tree but retained in history.

- [ ] **Step 5: Commit the release audit**

```powershell
git add scripts/audit_public_release.py tests/test_public_release_audit.py
git commit -m "test: add public release security audit"
```

### Task 9: Full Verification and Private Pull Request

**Files:**
- Modify only if verification exposes a regression.

- [ ] **Step 1: Run the release audit on the feature branch**

Run: `python scripts/audit_public_release.py --repo .`

Expected: `Public release audit passed` and exit code 0. If a finding exists, stop rollout, redact it without printing the value, rotate the affected credential, clean history when necessary, and rerun the audit.

- [ ] **Step 2: Run the complete automated suite**

Run: `python -m pytest -q`

Expected: all tests pass with the existing one intentional skip unless the suite count changes through added tests.

- [ ] **Step 3: Run a local Streamlit smoke server in public-demo mode**

Run:

```powershell
$env:WORKBENCH_DEPLOYMENT='public_demo'
streamlit run app_v2.py --server.headless true --server.port 8503
```

Expected: server reports `http://localhost:8503`; signed-out local browsing renders all five pages, Reference loading and Participant View work, Generation and Review mutations remain locked without an access code.

- [ ] **Step 4: Review the complete branch diff and secret-safe output**

Run:

```powershell
git diff master...HEAD --check
git status --short
git log --oneline master..HEAD
```

Expected: no whitespace errors, a clean worktree, and only public-demo access commits.

- [ ] **Step 5: Push and create a private pull request**

Run:

```powershell
git push -u origin codex/public-demo-access
gh pr create --base master --head codex/public-demo-access --title "feat: add protected public demo access" --body-file docs/superpowers/specs/2026-07-24-public-demo-access-design.md
```

Expected: push succeeds and GitHub returns a pull request URL. Keep the repository private at this point.

### Task 10: Controlled Public Rollout

**Files:**
- Modify: `README.md` only if the verified final Streamlit URL differs.

- [ ] **Step 1: Protect the current private deployment before merge**

In Streamlit Secrets, set `WORKBENCH_DEPLOYMENT = "research"` before merging so the existing private deployment preserves its durable behavior during the transition. Never put the secret values into Git or terminal output.

- [ ] **Step 2: Merge only after pull-request checks pass**

Run: `gh pr checks <PR-NUMBER>`

Expected: every required check passes. Merge through GitHub, then verify `origin/master` contains the feature commits.

- [ ] **Step 3: Run the audit again against the exact merged commit**

Run:

```powershell
git fetch origin
git switch master
git pull --ff-only
python scripts/audit_public_release.py --repo .
```

Expected: audit passes on the exact commit that will become public. A failure stops rollout.

- [ ] **Step 4: Configure capped public-demo secrets**

In Streamlit Community Cloud Secrets, set only:

```toml
WORKBENCH_DEPLOYMENT = "public_demo"
PUBLIC_DEMO_GENERATION_LIMIT = "3"
OPENAI_API_KEY = "<dedicated provider-capped demo credential>"
LLM_MODEL = "<provider model identifier>"
OPENAI_BASE_URL = "<compatible endpoint>"
LIVE_ACCESS_CODE = "<strong independent random access code>"
```

The demo credential must be separate from ordinary research use and capped at the provider. If the status of any previously shared key is uncertain, rotate it before this step.

- [ ] **Step 5: Make GitHub public, then enable public Streamlit sharing**

Change `YaoZeLiu0417/LLM_Psychometric` repository visibility to public only after Step 3 passes. Change the existing Streamlit app sharing to public, or redeploy from the public repository if Community Cloud requires it.

- [ ] **Step 6: Verify anonymous access and isolation**

In a signed-out/private browser:

- Open `https://adolescent-big-five-workbench.streamlit.app/`; it must not redirect to `/-/login`.
- Navigate all five pages.
- Load a reference item and complete Participant View.
- Confirm Generation and Review mutation controls remain locked.
- Confirm two JSON/CSV reference downloads work.
- In an unlocked test session, generate and review an item.
- Open a second fresh private session and confirm it still shows the original five reference items.
- Confirm provider telemetry records no model request from the anonymous session.

- [ ] **Step 7: Record the verified public link**

If the URL remains unchanged, no README edit is needed. If Streamlit assigns a new URL, update `README.md`, run `python -m pytest tests/test_readme.py -q`, commit, push, and wait for redeploy before giving the final URL to the owner.

- [ ] **Step 8: Apply rollback if any public check fails**

Immediately return Streamlit and GitHub visibility to private where possible, revoke or rotate the demo API key and access code, diagnose privately, then repeat the exact audit and anonymous verification. Treat any already-public Git history as potentially copied even after visibility is restored.
