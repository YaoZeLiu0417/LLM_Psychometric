# Adolescent Big Five Research Workbench V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver by 2026-07-24 a stable Streamlit V2 research workbench that migrates the legacy 60-item Big Five anchors, supports traceable staged item generation and review, and remains fully demonstrable offline with five Chinese adolescent items.

**Architecture:** Build a clean root-level `psychometric_v2` package and leave the legacy folder untouched. Streamlit is a thin view layer over typed Pydantic domain models, a JSON repository, deterministic quality checks, an OpenAI-compatible generation adapter, and a workbench service. Curated demo data and live generation use the same contracts so the demo fallback is truthful rather than a separate fake UI.

**Tech Stack:** Python 3.13, Streamlit 1.45, Pydantic 2.12, OpenAI Python 2.x, Plotly 5.24, python-dotenv, pytest 8.3, Streamlit AppTest, JSON/CSV, locally bundled Source Sans 3.

**Approved design:** `docs/superpowers/specs/2026-07-22-adolescent-big-five-workbench-design.md`

---

## File Map

Create these root files:

- `.gitignore`: protect credentials, runtime data, logs, and the untracked legacy archive.
- `.env.example`: document live-mode configuration without secrets.
- `requirements-v2.txt`: the lean dependency contract for V2.
- `pytest.ini`: test discovery and concise output.
- `app_v2.py`: Streamlit entry point only.
- `README_V2.md`: exact startup, demo, and verification instructions.
- `run_v2.ps1`: one-command Windows launcher.

Create these package files:

- `psychometric_v2/__init__.py`: package version.
- `psychometric_v2/config.py`: paths, environment loading, model configuration.
- `psychometric_v2/models.py`: all persisted and generated contracts.
- `psychometric_v2/taxonomy.py`: five domains, 15 facets, labels, definitions, and colors.
- `psychometric_v2/legacy.py`: read-only legacy JSONL discovery and migration.
- `psychometric_v2/demo_seed.py`: five curated adolescent demo candidates.
- `psychometric_v2/repository.py`: atomic JSON persistence and seed initialization.
- `psychometric_v2/quality.py`: deterministic item checks.
- `psychometric_v2/exports.py`: structured JSON and flattened CSV exports.
- `psychometric_v2/model_client.py`: OpenAI-compatible JSON client and explicit errors.
- `psychometric_v2/prompts.py`: stage-specific prompt builders.
- `psychometric_v2/pipeline.py`: construct, blueprint, option, and QA generation stages.
- `psychometric_v2/workbench.py`: application workflow and review-version transitions.
- `psychometric_v2/ui/__init__.py`: UI package marker.
- `psychometric_v2/ui/theme.py`: Alto-inspired CSS and embedded font loading.
- `psychometric_v2/ui/state.py`: namespaced Streamlit state initialization.
- `psychometric_v2/ui/components.py`: shared header, navigation, status, and provenance renderers.
- `psychometric_v2/ui/pages/project.py`: project overview and research lineage.
- `psychometric_v2/ui/pages/construct_map.py`: Plotly construct fingerprint and anchor browser.
- `psychometric_v2/ui/pages/generation.py`: staged generation studio.
- `psychometric_v2/ui/pages/review.py`: review queue, editor, checks, and version history.
- `psychometric_v2/ui/pages/participant.py`: five-item Chinese participant preview.
- `psychometric_v2/assets/data/bfi2_anchors.json`: clean migration of the legacy 60 items.
- `psychometric_v2/assets/fonts/SourceSans3-Variable.ttf`: bundled Latin font.
- `psychometric_v2/assets/fonts/OFL.txt`: font license.

Create matching tests under `tests/`:

- `test_models.py`
- `test_taxonomy.py`
- `test_legacy.py`
- `test_repository.py`
- `test_quality.py`
- `test_exports.py`
- `test_model_client.py`
- `test_pipeline.py`
- `test_workbench.py`
- `test_app_smoke.py`

Runtime writes go only to `workspace_data/v2/projects/`, which is ignored by Git.

## Task 1: Secure Root Scaffold

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `requirements-v2.txt`
- Create: `pytest.ini`
- Create: `psychometric_v2/__init__.py`
- Create: `tests/test_environment.py`

- [ ] **Step 1: Write the failing package smoke test**

```python
# tests/test_environment.py
from psychometric_v2 import __version__


def test_package_has_v2_version() -> None:
    assert __version__ == "2.0.0-demo"
```

- [ ] **Step 2: Run the smoke test and confirm the package is missing**

Run: `python -m pytest tests/test_environment.py -v`

Expected: collection fails with `ModuleNotFoundError: No module named 'psychometric_v2'`.

- [ ] **Step 3: Add the package marker and test configuration**

```python
# psychometric_v2/__init__.py
__version__ = "2.0.0-demo"
```

```ini
# pytest.ini
[pytest]
testpaths = tests
addopts = -q
```

```text
# requirements-v2.txt
streamlit>=1.45,<2
pydantic>=2.12,<3
openai>=2.8,<3
python-dotenv>=1.1,<2
pandas>=2.2,<3
plotly>=5.24,<6
pytest>=8.3,<9
```

```gitignore
# .gitignore
.env
.env.*
!.env.example
.streamlit/secrets.toml
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
workspace_data/
exports/
*.log

# Preserve the legacy project locally without accidentally versioning its
# credentials, logs, generated data, or mojibake paths.
/250705-问卷研究/
/250705-问卷研究.zip
```

```dotenv
# .env.example
OPENAI_API_KEY=
LLM_MODEL=
OPENAI_BASE_URL=
```

- [ ] **Step 4: Verify the environment contract**

Run: `python -m pip install -r requirements-v2.txt`

Expected: exit code 0 with the existing environment satisfying or updating the listed packages.

Run: `python -m pytest tests/test_environment.py -v`

Expected: `1 passed`.

- [ ] **Step 5: Commit only the scaffold**

```powershell
git add .gitignore .env.example requirements-v2.txt pytest.ini psychometric_v2/__init__.py tests/test_environment.py
git commit -m "chore: scaffold secure V2 workspace"
```

## Task 2: Define the Big Five Taxonomy and Domain Contracts

**Files:**
- Create: `psychometric_v2/taxonomy.py`
- Create: `psychometric_v2/models.py`
- Create: `tests/test_taxonomy.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing taxonomy tests**

```python
# tests/test_taxonomy.py
from psychometric_v2.taxonomy import DOMAINS, FACETS, LEGACY_FEATURE_MAP


def test_taxonomy_has_five_domains_and_fifteen_facets() -> None:
    assert len(DOMAINS) == 5
    assert len(FACETS) == 15
    assert {facet.domain_id for facet in FACETS.values()} == set(DOMAINS)


def test_every_legacy_feature_maps_to_one_facet() -> None:
    assert len(LEGACY_FEATURE_MAP) == 15
    assert set(LEGACY_FEATURE_MAP.values()) == set(FACETS)


def test_domain_palette_is_not_one_note() -> None:
    assert len({domain.color for domain in DOMAINS.values()}) == 5
```

- [ ] **Step 2: Write failing model-invariant tests**

```python
# tests/test_models.py
import pytest
from pydantic import ValidationError

from psychometric_v2.models import CandidateItem, EvidenceStatus, ResponseOption


def make_option(score: int, order: int) -> ResponseOption:
    return ResponseOption(
        option_id=f"o{score}",
        text_zh=f"行为选项{score}",
        trait_level=score,
        score=score,
        display_order=order,
        rationale=f"可观察行为水平{score}",
        desirability_note="无明显道德优劣",
    )


def test_candidate_requires_four_unique_score_levels() -> None:
    item = CandidateItem(
        item_id="item-1",
        domain_id="extraversion",
        facet_id="sociability",
        anchor_ids=["bfi2-sociability-01"],
        instruction_zh="如果是你，你最可能怎么做？",
        stem_zh="一次社团活动开始前，几位同学还不熟悉彼此。",
        options=[make_option(4, 1), make_option(1, 2), make_option(3, 3), make_option(2, 4)],
        evidence_status=EvidenceStatus.MODEL_DRAFT,
    )
    assert {option.score for option in item.options} == {1, 2, 3, 4}


def test_candidate_rejects_duplicate_scores() -> None:
    with pytest.raises(ValidationError):
        CandidateItem(
            item_id="item-1",
            domain_id="extraversion",
            facet_id="sociability",
            anchor_ids=["bfi2-sociability-01"],
            instruction_zh="如果是你，你最可能怎么做？",
            stem_zh="一次社团活动开始前，几位同学还不熟悉彼此。",
            options=[make_option(1, 1), make_option(1, 2), make_option(3, 3), make_option(4, 4)],
        )


def test_validated_is_not_an_allowed_evidence_status() -> None:
    assert "VALIDATED" not in {status.value for status in EvidenceStatus}
```

- [ ] **Step 3: Run both test files and confirm they fail**

Run: `python -m pytest tests/test_taxonomy.py tests/test_models.py -v`

Expected: import failures for `psychometric_v2.taxonomy` and `psychometric_v2.models`.

- [ ] **Step 4: Implement the complete taxonomy**

Create immutable `DomainDefinition` and `FacetDefinition` dataclasses. Define these exact domains and facets:

```python
# psychometric_v2/taxonomy.py
from dataclasses import dataclass


@dataclass(frozen=True)
class DomainDefinition:
    domain_id: str
    label_en: str
    label_zh: str
    legacy_label_zh: str
    color: str


@dataclass(frozen=True)
class FacetDefinition:
    facet_id: str
    domain_id: str
    label_en: str
    label_zh: str
    definition_zh: str


DOMAINS = {
    "extraversion": DomainDefinition("extraversion", "Extraversion", "外向性", "外向性", "#D81B78"),
    "agreeableness": DomainDefinition("agreeableness", "Agreeableness", "宜人性", "宜人性", "#24A8D8"),
    "conscientiousness": DomainDefinition("conscientiousness", "Conscientiousness", "尽责性", "尽责性", "#F28C28"),
    "negative_emotionality": DomainDefinition("negative_emotionality", "Negative Emotionality", "负性情绪", "神经质", "#E44B5F"),
    "open_mindedness": DomainDefinition("open_mindedness", "Open-Mindedness", "开放思维", "开放性", "#40358C"),
}


_FACET_ROWS = [
    ("sociability", "extraversion", "Sociability", "社交性", "主动接近他人并参与社会互动的倾向。"),
    ("assertiveness", "extraversion", "Assertiveness", "自信表达", "在群体中清楚表达观点并承担主动角色的倾向。"),
    ("energy_level", "extraversion", "Energy Level", "活力", "以积极节奏投入活动并保持行动能量的倾向。"),
    ("compassion", "agreeableness", "Compassion", "同情", "关注他人感受并愿意提供支持的倾向。"),
    ("respectfulness", "agreeableness", "Respectfulness", "尊重", "在分歧中遵守互动规范并尊重他人的倾向。"),
    ("trust", "agreeableness", "Trust", "信任", "倾向于相信他人的善意与合作意愿。"),
    ("organization", "conscientiousness", "Organization", "条理", "有序安排材料、步骤与时间的倾向。"),
    ("productiveness", "conscientiousness", "Productiveness", "效率", "持续推进任务并完成既定目标的倾向。"),
    ("responsibility", "conscientiousness", "Responsibility", "负责", "履行承诺并考虑行为后果的倾向。"),
    ("anxiety", "negative_emotionality", "Anxiety", "焦虑", "面对不确定或压力时产生担忧和紧张的倾向。"),
    ("depression", "negative_emotionality", "Depression", "低落", "经历挫折时出现低落和退缩体验的倾向。"),
    ("emotional_volatility", "negative_emotionality", "Emotional Volatility", "情绪易变", "情绪受到事件影响而快速或强烈变化的倾向。"),
    ("intellectual_curiosity", "open_mindedness", "Intellectual Curiosity", "求知好奇", "主动探索解释、新知识和复杂问题的倾向。"),
    ("aesthetic_sensitivity", "open_mindedness", "Aesthetic Sensitivity", "审美敏感", "注意并体验艺术与环境审美特征的倾向。"),
    ("creative_imagination", "open_mindedness", "Creative Imagination", "创造想象", "形成新颖联想、设想和表达方式的倾向。"),
]

FACETS = {row[0]: FacetDefinition(*row) for row in _FACET_ROWS}

LEGACY_FEATURE_MAP = {
    "外向性、社交": "sociability", "外向性、果断": "assertiveness", "外向性、活力": "energy_level",
    "宜人性、同情": "compassion", "宜人性、谦恭": "respectfulness", "宜人性、信任": "trust",
    "尽责性、条理": "organization", "尽责性、效率": "productiveness", "尽责性、负责": "responsibility",
    "神经质、焦虑": "anxiety", "神经质、抑郁": "depression", "神经质、易变": "emotional_volatility",
    "开放性、好奇": "intellectual_curiosity", "开放性、审美": "aesthetic_sensitivity", "开放性、想象": "creative_imagination",
}
```

- [ ] **Step 5: Implement the persisted models and invariants**

Use `str, Enum` enums for `GenerationMode`, `EvidenceStatus`, `CheckSeverity`, `CheckOutcome`, and `ReviewAction`. Implement Pydantic models with these required contracts:

```python
# psychometric_v2/models.py
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GenerationMode(str, Enum):
    LIVE = "LIVE GENERATION"
    CURATED = "CURATED DEMO"


class EvidenceStatus(str, Enum):
    MODEL_DRAFT = "MODEL_DRAFT"
    NEEDS_REVISION = "NEEDS_REVISION"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    PILOT_CANDIDATE = "PILOT_CANDIDATE"


class CheckSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CheckOutcome(str, Enum):
    PASS = "PASS"
    FLAG = "FLAG"


class ReviewAction(str, Enum):
    EDIT = "EDIT"
    RETURN = "RETURN"
    APPROVE = "APPROVE"
    PROMOTE_TO_PILOT = "PROMOTE_TO_PILOT"


class ProjectConfig(BaseModel):
    project_id: str
    title: str
    population: str = "Mainland Chinese junior-secondary students"
    age_min: int = 12
    age_max: int = 15
    locale: str = "zh-CN"
    context_domains: list[str] = Field(default_factory=lambda: ["classroom", "group_work", "peer", "family", "club", "online"])
    instruction_zh: str = "如果是你，你最可能怎么做？"
    prompt_version: str = "v2.0-demo"


class ConstructAnchor(BaseModel):
    anchor_id: str
    item_number: int
    text_zh: str
    legacy_feature: str
    domain_id: str
    facet_id: str
    reverse: bool
    source: str = "legacy_big_five_60"


class ConstructSpecification(BaseModel):
    domain_id: str
    facet_id: str
    anchor_ids: list[str]
    definition_zh: str
    behavioral_indicators: list[str]
    exclusions: list[str]
    potential_confounds: list[str]


class ScenarioBlueprint(BaseModel):
    setting: str
    actors: list[str]
    relationship: str
    goal: str
    trigger_event: str
    decision_point: str
    context_domain: str


class ResponseOption(BaseModel):
    option_id: str
    text_zh: str
    trait_level: int = Field(ge=1, le=4)
    score: int = Field(ge=1, le=4)
    display_order: int = Field(ge=1, le=4)
    rationale: str
    desirability_note: str


class QualityCheck(BaseModel):
    check_id: str
    label: str
    severity: CheckSeverity
    outcome: CheckOutcome
    evidence: str
    recommendation: str = ""


class ReviewVersion(BaseModel):
    version: int
    created_at: str = Field(default_factory=utc_now_iso)
    reviewer: str
    action: ReviewAction
    note: str
    before_stem_zh: str
    before_options: list[ResponseOption]
    after_stem_zh: str
    after_options: list[ResponseOption]


class CandidateItem(BaseModel):
    item_id: str
    domain_id: str
    facet_id: str
    anchor_ids: list[str] = Field(min_length=1)
    instruction_zh: str
    stem_zh: str
    construct_spec: ConstructSpecification | None = None
    scenario_blueprint: ScenarioBlueprint | None = None
    options: list[ResponseOption]
    quality_checks: list[QualityCheck] = Field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.MODEL_DRAFT
    generation_mode: GenerationMode = GenerationMode.CURATED
    model_id: str | None = None
    prompt_version: str = "v2.0-demo"
    created_at: str = Field(default_factory=utc_now_iso)
    review_versions: list[ReviewVersion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_options(self) -> "CandidateItem":
        if len(self.options) != 4:
            raise ValueError("candidate items require exactly four options")
        if {option.score for option in self.options} != {1, 2, 3, 4}:
            raise ValueError("option scores must cover 1, 2, 3, and 4")
        if {option.display_order for option in self.options} != {1, 2, 3, 4}:
            raise ValueError("display order must cover 1, 2, 3, and 4")
        if len({option.text_zh.strip() for option in self.options}) != 4:
            raise ValueError("option text must be unique")
        return self


class ResearchProject(BaseModel):
    config: ProjectConfig
    items: dict[str, CandidateItem] = Field(default_factory=dict)
    selected_item_id: str | None = None
    updated_at: str = Field(default_factory=utc_now_iso)


class GenerationMetadata(BaseModel):
    model_id: str
    prompt_version: str
    generated_at: str = Field(default_factory=utc_now_iso)
    constraint_snapshot: dict[str, Any]
```

- [ ] **Step 6: Run the domain tests**

Run: `python -m pytest tests/test_taxonomy.py tests/test_models.py -v`

Expected: all tests pass.

- [ ] **Step 7: Commit the contracts**

```powershell
git add psychometric_v2/taxonomy.py psychometric_v2/models.py tests/test_taxonomy.py tests/test_models.py
git commit -m "feat: define Big Five V2 domain contracts"
```

## Task 3: Migrate the Legacy 60-Item Asset

**Files:**
- Create: `psychometric_v2/legacy.py`
- Create: `scripts/migrate_legacy_anchors.py`
- Create: `psychometric_v2/assets/data/bfi2_anchors.json`
- Create: `tests/test_legacy.py`

- [ ] **Step 1: Write failing migration tests with a temporary JSONL fixture**

```python
# tests/test_legacy.py
import json
from pathlib import Path

from psychometric_v2.legacy import migrate_anchor_file


def test_migration_preserves_text_feature_and_reverse(tmp_path: Path) -> None:
    source = tmp_path / "anchors.jsonl"
    rows = [
        {"question": "我喜欢与人交往。", "feature": "外向性、社交", "reverse": False},
        {"question": "我通常保持安静。", "feature": "外向性、社交", "reverse": True},
    ]
    source.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    anchors = migrate_anchor_file(source)

    assert [anchor.anchor_id for anchor in anchors] == ["bfi2-sociability-01", "bfi2-sociability-02"]
    assert anchors[0].text_zh == "我喜欢与人交往。"
    assert anchors[1].reverse is True
    assert anchors[0].domain_id == "extraversion"
```

- [ ] **Step 2: Run the migration test and confirm failure**

Run: `python -m pytest tests/test_legacy.py -v`

Expected: import failure for `psychometric_v2.legacy`.

- [ ] **Step 3: Implement read-only discovery and migration**

```python
# psychometric_v2/legacy.py
import json
from collections import defaultdict
from pathlib import Path

from psychometric_v2.models import ConstructAnchor
from psychometric_v2.taxonomy import FACETS, LEGACY_FEATURE_MAP


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def discover_legacy_anchor_file(root: Path) -> Path:
    candidates: list[Path] = []
    for path in root.rglob("*.jsonl"):
        try:
            rows = read_jsonl(path)
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        features = {row.get("feature") for row in rows}
        if len(rows) == 60 and features == set(LEGACY_FEATURE_MAP):
            candidates.append(path)
    if not candidates:
        raise FileNotFoundError("no 60-item legacy Big Five JSONL was found")
    candidates.sort(key=lambda path: (path.parent.name != "data", len(str(path)), str(path)))
    return candidates[0]


def migrate_anchor_file(path: Path) -> list[ConstructAnchor]:
    counters: dict[str, int] = defaultdict(int)
    anchors: list[ConstructAnchor] = []
    for item_number, row in enumerate(read_jsonl(path), start=1):
        facet_id = LEGACY_FEATURE_MAP[row["feature"]]
        counters[facet_id] += 1
        anchors.append(
            ConstructAnchor(
                anchor_id=f"bfi2-{facet_id}-{counters[facet_id]:02d}",
                item_number=item_number,
                text_zh=row["question"].strip(),
                legacy_feature=row["feature"],
                domain_id=FACETS[facet_id].domain_id,
                facet_id=facet_id,
                reverse=bool(row.get("reverse", False)),
            )
        )
    return anchors


def write_anchor_asset(anchors: list[ConstructAnchor], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps([anchor.model_dump(mode="json") for anchor in anchors], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_anchor_asset(path: Path) -> dict[str, ConstructAnchor]:
    anchors = [ConstructAnchor.model_validate(row) for row in json.loads(path.read_text(encoding="utf-8"))]
    return {anchor.anchor_id: anchor for anchor in anchors}
```

```python
# scripts/migrate_legacy_anchors.py
from pathlib import Path

from psychometric_v2.legacy import discover_legacy_anchor_file, migrate_anchor_file, write_anchor_asset


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "psychometric_v2" / "assets" / "data" / "bfi2_anchors.json"


if __name__ == "__main__":
    source = discover_legacy_anchor_file(ROOT)
    anchors = migrate_anchor_file(source)
    if len(anchors) != 60:
        raise SystemExit(f"expected 60 anchors, received {len(anchors)}")
    if sum(anchor.reverse for anchor in anchors) != 30:
        raise SystemExit("expected 30 reverse-keyed anchors")
    write_anchor_asset(anchors, DESTINATION)
    print(f"Migrated {len(anchors)} anchors from {source} to {DESTINATION}")
```

- [ ] **Step 4: Run the migration test**

Run: `python -m pytest tests/test_legacy.py -v`

Expected: pass.

- [ ] **Step 5: Generate and verify the clean asset**

Run: `python scripts/migrate_legacy_anchors.py`

Expected: output contains `Migrated 60 anchors from` and ends with `psychometric_v2\assets\data\bfi2_anchors.json`.

Run: `python -c "import json; from pathlib import Path; a=json.loads(Path('psychometric_v2/assets/data/bfi2_anchors.json').read_text(encoding='utf-8')); print(len(a), sum(x['reverse'] for x in a), len({x['facet_id'] for x in a}))"`

Expected: `60 30 15`.

- [ ] **Step 6: Commit the migrated research asset**

```powershell
git add psychometric_v2/legacy.py scripts/migrate_legacy_anchors.py psychometric_v2/assets/data/bfi2_anchors.json tests/test_legacy.py
git commit -m "feat: migrate legacy Big Five anchors"
```

## Task 4: Curated Demo, Repository, Quality Checks, and Exports

**Files:**
- Create: `psychometric_v2/demo_seed.py`
- Create: `psychometric_v2/repository.py`
- Create: `psychometric_v2/quality.py`
- Create: `psychometric_v2/exports.py`
- Create: `tests/test_repository.py`
- Create: `tests/test_quality.py`
- Create: `tests/test_exports.py`

- [ ] **Step 1: Write failing repository and seed tests**

```python
# tests/test_repository.py
from pathlib import Path

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.repository import JsonProjectRepository


def test_demo_seed_has_one_item_per_domain() -> None:
    project = build_demo_project()
    assert len(project.items) == 5
    assert {item.domain_id for item in project.items.values()} == {
        "extraversion", "agreeableness", "conscientiousness", "negative_emotionality", "open_mindedness"
    }
    assert all(item.evidence_status.value == "MODEL_DRAFT" for item in project.items.values())


def test_repository_round_trip_is_lossless(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path)
    project = build_demo_project()
    repository.save(project)
    assert repository.load(project.config.project_id) == project
    assert not list(tmp_path.glob("*.tmp"))
```

- [ ] **Step 2: Write failing deterministic-quality and export tests**

```python
# tests/test_quality.py
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.quality import run_deterministic_checks


def test_curated_items_pass_structural_checks() -> None:
    for item in build_demo_project().items.values():
        checks = run_deterministic_checks(item)
        assert all(check.outcome.value == "PASS" for check in checks if check.severity.value == "ERROR")
```

```python
# tests/test_exports.py
import csv
import io
import json

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.exports import project_csv_bytes, project_json_bytes


def test_json_export_keeps_provenance_and_hides_no_fields() -> None:
    payload = json.loads(project_json_bytes(build_demo_project()).decode("utf-8"))
    first = next(iter(payload["items"].values()))
    assert first["anchor_ids"]
    assert first["scenario_blueprint"]["trigger_event"]


def test_csv_export_has_twenty_option_rows() -> None:
    rows = list(csv.DictReader(io.StringIO(project_csv_bytes(build_demo_project()).decode("utf-8-sig"))))
    assert len(rows) == 20
    assert {row["score"] for row in rows} == {"1", "2", "3", "4"}
```

- [ ] **Step 3: Run the tests and confirm missing modules**

Run: `python -m pytest tests/test_repository.py tests/test_quality.py tests/test_exports.py -v`

Expected: import failures for the four new modules.

- [ ] **Step 4: Implement the five exact curated candidates**

Create `build_demo_project()` with one candidate per domain. Use these exact scenario stems and score meanings; store the options in the listed display order so visible order does not reveal score:

```python
# psychometric_v2/demo_seed.py (content table used by build_demo_project)
DEMO_ROWS = [
    {
        "item_id": "demo-extraversion-sociability",
        "domain_id": "extraversion", "facet_id": "sociability", "anchor_id": "bfi2-sociability-01",
        "setting": "新学期社团第一次小组活动", "actors": ["你", "几位不同班的同学"],
        "relationship": "初次见面的同龄人", "goal": "完成分组并开始活动",
        "trigger": "老师让大家自行认识并组成三人小组", "decision": "决定如何进入同伴互动",
        "stem": "新学期社团第一次活动，老师请大家自行认识并组成三人小组。周围大多是不同班、还不熟悉的同学。这时你最可能：",
        "options": [
            ("ext-b", "先观察大家的交流，等有人邀请时再加入", 2, "被邀请后参与互动"),
            ("ext-d", "主动和附近几位同学打招呼，并邀请大家一起组队", 4, "主动发起并扩展互动"),
            ("ext-a", "先找一位看起来容易交流的同学聊几句", 3, "主动建立一对一互动"),
            ("ext-c", "先看看活动材料，等分组快结束时再决定", 1, "保持低社交发起水平"),
        ],
    },
    {
        "item_id": "demo-agreeableness-respectfulness",
        "domain_id": "agreeableness", "facet_id": "respectfulness", "anchor_id": "bfi2-respectfulness-01",
        "setting": "课堂小组方案讨论", "actors": ["你", "小组同学"],
        "relationship": "共同完成任务的同伴", "goal": "确定小组展示方案",
        "trigger": "一位同学提出了与你不同的方案", "decision": "决定如何表达分歧",
        "stem": "小组正在确定课堂展示方案。一位同学提出的做法与你的想法差别很大，但留给大家讨论的时间不多。这时你最可能：",
        "options": [
            ("agr-c", "直接说明自己方案的优势，希望大家尽快采用", 2, "表达分歧时较少协调他人观点"),
            ("agr-a", "先问清对方的理由，再说明自己的考虑并寻找可以结合的部分", 4, "在分歧中充分尊重并协调观点"),
            ("agr-d", "在对方解释时不断指出问题，坚持自己的方案更合适", 1, "较少为对方保留完整表达空间"),
            ("agr-b", "礼貌说明自己不同意的地方，然后请全组一起比较两种方案", 3, "以规范方式表达分歧"),
        ],
    },
    {
        "item_id": "demo-conscientiousness-organization",
        "domain_id": "conscientiousness", "facet_id": "organization", "anchor_id": "bfi2-organization-01",
        "setting": "一周内有多项学习任务", "actors": ["你"], "relationship": "个人任务管理",
        "goal": "按时完成作业、测验准备和小组材料", "trigger": "发现三项任务集中在同一周截止",
        "decision": "决定如何安排开始顺序", "stem": "你发现本周同时要交两份作业、准备一次小测，还要完成小组展示材料。这时你最可能：",
        "options": [
            ("con-b", "先处理截止时间最近的任务，其余任务边做边调整", 3, "有基本优先顺序"),
            ("con-d", "先做自己最想做的部分，之后再看剩余时间怎么安排", 1, "主要依即时偏好安排任务"),
            ("con-a", "列出每项任务的截止时间和所需步骤，再安排每天的进度", 4, "系统组织时间与步骤"),
            ("con-c", "记住各项截止时间，有空时选择其中一项推进", 2, "有截止意识但组织程度有限"),
        ],
    },
    {
        "item_id": "demo-negative-emotionality-anxiety",
        "domain_id": "negative_emotionality", "facet_id": "anxiety", "anchor_id": "bfi2-anxiety-01",
        "setting": "课堂展示临时返工", "actors": ["你", "任课老师"], "relationship": "学生与教师",
        "goal": "第二天完成修改后的展示", "trigger": "老师临时要求重做一个关键部分",
        "decision": "决定如何面对突然增加的不确定性", "stem": "放学前，老师告诉你明天的课堂展示有一个关键部分需要重新准备，而你原本以为已经完成了。这时你最可能：",
        "options": [
            ("neg-c", "有些担心时间不够，但先确认要求再开始修改", 2, "短暂担忧后恢复行动"),
            ("neg-a", "不断想着可能来不及，开始修改时也很难集中注意", 4, "担忧持续并干扰行动"),
            ("neg-d", "先整理需要改动的内容，按剩余时间重新安排", 1, "面对不确定性保持较低焦虑"),
            ("neg-b", "明显紧张，需要先缓一会儿才能着手处理", 3, "较强紧张并延迟行动"),
        ],
    },
    {
        "item_id": "demo-open-mindedness-curiosity",
        "domain_id": "open_mindedness", "facet_id": "intellectual_curiosity", "anchor_id": "bfi2-intellectual_curiosity-01",
        "setting": "科学课实验结果异常", "actors": ["你", "实验搭档"], "relationship": "共同实验的同伴",
        "goal": "理解实验结果", "trigger": "实验结果与课本预测不一致", "decision": "决定如何处理异常结果",
        "stem": "科学课实验结束后，你们得到的结果与课本上的预测不一致，实验步骤看起来也没有明显错误。这时你最可能：",
        "options": [
            ("open-d", "记录老师给出的正确结果，不再继续追究原因", 1, "较少继续探索解释"),
            ("open-b", "重新检查关键步骤，并向老师询问可能的原因", 3, "主动检查并寻求解释"),
            ("open-a", "提出几种可能解释，查找资料并尝试设计一个小验证", 4, "扩展解释并主动验证"),
            ("open-c", "和搭档讨论哪里可能不同，然后按课堂要求完成记录", 2, "有限探索后回到既定任务"),
        ],
    },
]
```

`build_demo_project()` must turn every row into a `ConstructSpecification`, `ScenarioBlueprint`, four `ResponseOption` objects with `display_order` from list position, and a `CandidateItem` in `MODEL_DRAFT` / `CURATED DEMO`. Use `desirability_note="各选项均为可理解的行为选择，不代表道德正确性"`. Build behavioral indicators from the score-3 and score-4 rationales, use exclusions `["学业能力高低", "道德好坏评价"]`, and use these exact confounds: sociability `["自信表达", "社交焦虑"]`; respectfulness `["冲突回避", "自信表达"]`; organization `["学习能力", "服从性"]`; anxiety `["实际任务难度", "短暂应激"]`; intellectual curiosity `["学科成绩", "课堂服从"]`. Run `run_deterministic_checks()` and store the returned checks on each item. Do not create a human review record in the seed.

- [ ] **Step 5: Implement atomic JSON persistence**

```python
# psychometric_v2/repository.py
import os
from pathlib import Path

from psychometric_v2.models import ResearchProject


class JsonProjectRepository:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, project_id: str) -> Path:
        return self.root / f"{project_id}.json"

    def save(self, project: ResearchProject) -> Path:
        destination = self.path_for(project.config.project_id)
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, destination)
        return destination

    def load(self, project_id: str) -> ResearchProject:
        return ResearchProject.model_validate_json(self.path_for(project_id).read_text(encoding="utf-8"))

    def ensure_seed(self, project: ResearchProject) -> ResearchProject:
        path = self.path_for(project.config.project_id)
        if not path.exists():
            self.save(project)
        return self.load(project.config.project_id)
```

- [ ] **Step 6: Implement deterministic checks and exports**

`run_deterministic_checks(item)` must return checks for `OPTION_COUNT`, `SCORE_COVERAGE`, `DISPLAY_ORDER`, `DUPLICATE_OPTIONS`, `OPTION_LENGTH_BALANCE`, and `PROVENANCE`. Mark structural failures as `ERROR`; length ratio above 2.2 as `WARNING`. JSON export uses `project.model_dump_json(indent=2).encode("utf-8")`. CSV uses Python's `csv.DictWriter`, emits one row per option, and encodes with `utf-8-sig`; columns are `item_id,domain_id,facet_id,anchor_ids,stem_zh,option_id,option_text_zh,trait_level,score,display_order,evidence_status,generation_mode`.

- [ ] **Step 7: Run repository, quality, and export tests**

Run: `python -m pytest tests/test_repository.py tests/test_quality.py tests/test_exports.py -v`

Expected: all tests pass.

- [ ] **Step 8: Commit the offline demo core**

```powershell
git add psychometric_v2/demo_seed.py psychometric_v2/repository.py psychometric_v2/quality.py psychometric_v2/exports.py tests/test_repository.py tests/test_quality.py tests/test_exports.py
git commit -m "feat: add curated adolescent demo core"
```

## Task 5: Model Adapter, Prompts, Pipeline, and Review Workflow

**Files:**
- Create: `psychometric_v2/config.py`
- Create: `psychometric_v2/model_client.py`
- Create: `psychometric_v2/prompts.py`
- Create: `psychometric_v2/pipeline.py`
- Create: `psychometric_v2/workbench.py`
- Create: `tests/test_model_client.py`
- Create: `tests/test_pipeline.py`
- Create: `tests/test_workbench.py`

- [ ] **Step 1: Write failing model-configuration and retry tests**

```python
# tests/test_model_client.py
import pytest

from psychometric_v2.model_client import LiveModelConfig, ModelUnavailable


def test_live_mode_requires_key_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(ModelUnavailable):
        LiveModelConfig.from_env()


def test_timeout_is_translated_to_public_error() -> None:
    from psychometric_v2.model_client import ModelTimeout, OpenAICompatibleClient

    class TimeoutCompletions:
        def create(self, **kwargs):
            raise TimeoutError("private transport detail")

    class FakeClient:
        class Chat:
            completions = TimeoutCompletions()
        chat = Chat()

    config = LiveModelConfig(api_key="test", model_id="test-model", timeout_seconds=1)
    client = OpenAICompatibleClient(config, client=FakeClient())
    with pytest.raises(ModelTimeout, match="timed out"):
        client.complete_json("system", "user")


def test_invalid_json_is_translated_to_output_error() -> None:
    from types import SimpleNamespace
    from psychometric_v2.model_client import ModelOutputError, OpenAICompatibleClient

    class InvalidCompletions:
        def create(self, **kwargs):
            message = SimpleNamespace(content="not-json")
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class FakeClient:
        class Chat:
            completions = InvalidCompletions()
        chat = Chat()

    config = LiveModelConfig(api_key="test", model_id="test-model", timeout_seconds=1)
    client = OpenAICompatibleClient(config, client=FakeClient())
    with pytest.raises(ModelOutputError, match="valid structured output"):
        client.complete_json("system", "user")
```

```python
# tests/test_pipeline.py
import pytest

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.pipeline import GenerationPipeline, GenerationStageError


class QueueClient:
    model_id = "fake-model"

    def __init__(self, responses: list[dict]):
        self.responses = responses

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        return self.responses.pop(0)


def test_pipeline_repairs_one_invalid_option_response() -> None:
    project = build_demo_project()
    client = QueueClient([
        {"definition_zh": "定义", "behavioral_indicators": ["行为"], "exclusions": ["排除"], "potential_confounds": ["混淆"]},
        {"setting": "课堂", "actors": ["你", "同学"], "relationship": "同伴", "goal": "完成任务", "trigger_event": "出现分歧", "decision_point": "选择回应", "context_domain": "group_work"},
        {"stem_zh": "小组活动开始前，你需要决定如何加入同伴。", "options": [{"text_zh": "只有一个选项"}]},
        {"stem_zh": "小组活动开始前，你需要决定如何加入同伴。这时你最可能：", "options": [
            {"option_id": "a", "text_zh": "行为一", "trait_level": 1, "score": 1, "display_order": 2, "rationale": "低", "desirability_note": "中性"},
            {"option_id": "b", "text_zh": "行为二", "trait_level": 2, "score": 2, "display_order": 4, "rationale": "中低", "desirability_note": "中性"},
            {"option_id": "c", "text_zh": "行为三", "trait_level": 3, "score": 3, "display_order": 1, "rationale": "中高", "desirability_note": "中性"},
            {"option_id": "d", "text_zh": "行为四", "trait_level": 4, "score": 4, "display_order": 3, "rationale": "高", "desirability_note": "中性"},
        ]},
        {"checks": [
            {"check_id": "AGE_FIT", "label": "Age appropriateness", "severity": "INFO", "outcome": "PASS", "evidence": "使用同伴小组情境和初中生可理解语言", "recommendation": ""},
            {"check_id": "SOCIAL_DESIRABILITY", "label": "Social desirability", "severity": "WARNING", "outcome": "FLAG", "evidence": "主动选项可能略显积极", "recommendation": "人工检查四个选项的可接受性"},
        ]},
    ])
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")
    item = pipeline.generate_candidate(project.config, anchor, "peer")
    assert len(item.options) == 4
    assert item.model_id == "fake-model"
    assert any(check.check_id == "AGE_FIT" for check in item.quality_checks)


def test_pipeline_stops_after_one_failed_repair() -> None:
    project = build_demo_project()
    client = QueueClient([
        {"definition_zh": "定义", "behavioral_indicators": ["行为"], "exclusions": ["排除"], "potential_confounds": ["混淆"]},
        {"setting": "课堂", "actors": ["你", "同学"], "relationship": "同伴", "goal": "完成任务", "trigger_event": "出现分歧", "decision_point": "选择回应", "context_domain": "group_work"},
        {"stem_zh": "题干", "options": []},
        {"stem_zh": "题干", "options": []},
    ])
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")
    with pytest.raises(GenerationStageError, match="response options"):
        pipeline.generate_candidate(project.config, anchor, "peer")
```

- [ ] **Step 2: Write failing review-version tests**

```python
# tests/test_workbench.py
from pathlib import Path

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import EvidenceStatus, ReviewAction
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.workbench import WorkbenchService


def test_review_edit_creates_immutable_version(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path)
    project = build_demo_project()
    repository.save(project)
    service = WorkbenchService(repository)
    item_id = "demo-extraversion-sociability"
    original = project.items[item_id].stem_zh

    updated = service.review_item(
        project.config.project_id, item_id, original + "（修改）", project.items[item_id].options,
        reviewer="Researcher", action=ReviewAction.EDIT, note="现场演示修改",
    )

    assert updated.review_versions[-1].before_stem_zh == original
    assert updated.review_versions[-1].after_stem_zh == original + "（修改）"
    assert updated.evidence_status == EvidenceStatus.NEEDS_REVISION


def test_approve_never_implies_validation(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path)
    project = build_demo_project()
    repository.save(project)
    item = project.items["demo-extraversion-sociability"]
    updated = WorkbenchService(repository).review_item(
        project.config.project_id, item.item_id, item.stem_zh, item.options,
        reviewer="Researcher", action=ReviewAction.APPROVE, note="内容审核通过",
    )
    assert updated.evidence_status == EvidenceStatus.HUMAN_REVIEWED
```

- [ ] **Step 3: Run the tests and confirm the modules are missing**

Run: `python -m pytest tests/test_model_client.py tests/test_pipeline.py tests/test_workbench.py -v`

Expected: import failures.

- [ ] **Step 4: Implement secure root-only configuration and the OpenAI-compatible client**

`config.py` defines `ROOT`, `ANCHOR_ASSET`, `FONT_ASSET`, and `WORKSPACE_ROOT`, and calls `load_dotenv(ROOT / ".env", override=False)` only; it must not scan parent directories or the legacy tree. `LiveModelConfig.from_env()` requires `OPENAI_API_KEY` and `LLM_MODEL`, accepts `OPENAI_BASE_URL` then legacy `OPENAI_API_BASE`, and uses a 45-second timeout.

`OpenAICompatibleClient.complete_json()` calls `client.chat.completions.create()` with system and user messages, `temperature=0.35`, and `response_format={"type": "json_object"}`. Parse `response.choices[0].message.content` with `json.loads`. Raise `ModelUnavailable`, `ModelTimeout`, or `ModelOutputError`; never print the request, response, API key, or raw exception into the UI.

- [ ] **Step 5: Implement explicit prompts without chain-of-thought requests**

Create `construct_prompt(anchor, facet, config)`, `blueprint_prompt(spec, config, context_domain)`, `options_prompt(spec, blueprint, config)`, and `quality_prompt(item, config)`. Each returns `(system_prompt, user_prompt)`, asks only for the corresponding JSON fields, includes the 12-15 age/context constraints, forbids direct trait naming in participant text, and asks for concise observable rationales rather than hidden reasoning. `quality_prompt` requests age fit, ecological plausibility, construct alignment, confounds, distinguishability, social desirability, answer obviousness, language complexity, and safety as structured `QualityCheck` rows.

- [ ] **Step 6: Implement the staged pipeline with one repair attempt**

`GenerationPipeline` loads anchors from `psychometric_v2/assets/data/bfi2_anchors.json`, validates each stage with Pydantic, and makes at most two calls per stage. It fills domain, facet, and anchor IDs from the selected anchor rather than trusting model output. The option stage requires both `stem_zh` and four options. After deterministic checks, call the model-assisted quality stage and append its validated checks. On first validation failure, append the validation message and exact schema to a repair prompt. On second failure, raise `GenerationStageError(stage, public_message)` while retaining previously returned stage objects in Streamlit state. Construct the final `CandidateItem` in `MODEL_DRAFT` / `LIVE GENERATION`, run deterministic checks, and store model ID and prompt version.

- [ ] **Step 7: Implement repository-backed review transitions**

`WorkbenchService.review_item()` accepts project ID, item ID, edited stem, edited `ResponseOption` list, reviewer, action, and note. Append a new numbered `ReviewVersion` containing both the prior and resulting stem/options; set `EDIT`/`RETURN` to `NEEDS_REVISION`, `APPROVE` to `HUMAN_REVIEWED`, and `PROMOTE_TO_PILOT` to `PILOT_CANDIDATE` only from `HUMAN_REVIEWED`. Re-run deterministic checks and atomically save. No transition may produce a validated label.

- [ ] **Step 8: Run all service tests**

Run: `python -m pytest tests/test_model_client.py tests/test_pipeline.py tests/test_workbench.py -v`

Expected: all tests pass without a real API call.

- [ ] **Step 9: Commit the live and review core**

```powershell
git add psychometric_v2/config.py psychometric_v2/model_client.py psychometric_v2/prompts.py psychometric_v2/pipeline.py psychometric_v2/workbench.py tests/test_model_client.py tests/test_pipeline.py tests/test_workbench.py
git commit -m "feat: add traceable generation and review workflow"
```

## Task 6: Build the Alto-Inspired Shell, PROJECT, and CONSTRUCT MAP

**Files:**
- Create: `psychometric_v2/assets/fonts/SourceSans3-Variable.ttf`
- Create: `psychometric_v2/assets/fonts/OFL.txt`
- Create: `psychometric_v2/ui/__init__.py`
- Create: `psychometric_v2/ui/theme.py`
- Create: `psychometric_v2/ui/state.py`
- Create: `psychometric_v2/ui/components.py`
- Create: `psychometric_v2/ui/pages/__init__.py`
- Create: `psychometric_v2/ui/pages/project.py`
- Create: `psychometric_v2/ui/pages/construct_map.py`
- Create: `psychometric_v2/ui/pages/generation.py`
- Create: `psychometric_v2/ui/pages/review.py`
- Create: `psychometric_v2/ui/pages/participant.py`
- Create: `app_v2.py`
- Create: `tests/test_app_smoke.py`

- [ ] **Step 1: Download the licensed font assets**

Run:

```powershell
New-Item -ItemType Directory -Force psychometric_v2/assets/fonts
Invoke-WebRequest 'https://raw.githubusercontent.com/google/fonts/main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf' -OutFile 'psychometric_v2/assets/fonts/SourceSans3-Variable.ttf'
Invoke-WebRequest 'https://raw.githubusercontent.com/google/fonts/main/ofl/sourcesans3/OFL.txt' -OutFile 'psychometric_v2/assets/fonts/OFL.txt'
```

Expected: both files exist and `SourceSans3-Variable.ttf` is larger than 100 KB.

- [ ] **Step 2: Write a failing AppTest smoke test**

```python
# tests/test_app_smoke.py
from streamlit.testing.v1 import AppTest


def test_app_starts_in_curated_mode_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    app = AppTest.from_file("app_v2.py", default_timeout=15).run()
    assert not app.exception
    assert any("Adolescent Big Five" in markdown.value for markdown in app.markdown)
    assert any("CURATED DEMO" in markdown.value for markdown in app.markdown)
```

- [ ] **Step 3: Run the smoke test and confirm app entry is absent**

Run: `python -m pytest tests/test_app_smoke.py -v`

Expected: failure because `app_v2.py` does not exist.

- [ ] **Step 4: Implement theme and namespaced state**

`theme.py` reads the local TTF, base64-embeds it in `@font-face`, and injects CSS tokens `#0B0B0D`, `#F7F7F5`, `#202124`, `#D81B78`, `#24A8D8`, `#F28C28`, and `#40358C`. Set Latin text to `Source Sans 3`; Chinese content classes use `Microsoft YaHei, Noto Sans SC, sans-serif`. Use zero letter spacing, 8px maximum radius, compact 15-17px body type, 28-36px workbench headings, a black header, and responsive rules for 1280px and 600px widths.

`state.py` initializes only keys prefixed `v2_`: active page, generation mode, selected domain/facet/item, generation stage objects, participant index, and participant responses. No page may invent additional unnamespaced keys.

- [ ] **Step 5: Implement shared components and app entry**

Create `components.py` with these complete shared renderers:

```python
# psychometric_v2/ui/components.py
import html

import streamlit as st

from psychometric_v2.models import CandidateItem, ConstructAnchor, EvidenceStatus, GenerationMode


PAGES = ["PROJECT", "CONSTRUCT MAP", "GENERATION STUDIO", "REVIEW", "PARTICIPANT VIEW"]
STAGES = ["CONSTRUCT SPECIFICATION", "SCENARIO BLUEPRINT", "RESPONSE OPTIONS", "QUALITY CHECKS"]
STATUS_COLORS = {
    EvidenceStatus.MODEL_DRAFT: "#24A8D8",
    EvidenceStatus.NEEDS_REVISION: "#F28C28",
    EvidenceStatus.HUMAN_REVIEWED: "#D81B78",
    EvidenceStatus.PILOT_CANDIDATE: "#40358C",
}


def render_header(project_title: str, mode: GenerationMode) -> None:
    st.markdown(
        f"""
        <div class="v2-header">
          <div><span class="v2-kicker">PSYCHOMETRIC WORKBENCH</span><br>{html.escape(project_title)}</div>
          <span class="v2-mode">{html.escape(mode.value)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_navigation(active_page: str) -> str:
    selected = st.segmented_control(
        "Workspace",
        PAGES,
        default=active_page,
        key="v2_navigation",
        label_visibility="collapsed",
    )
    return selected or active_page


def render_status(status: EvidenceStatus) -> None:
    color = STATUS_COLORS[status]
    st.markdown(
        f'<span class="v2-status" style="border-color:{color};color:{color}">{status.value}</span>',
        unsafe_allow_html=True,
    )


def render_provenance(item: CandidateItem, anchors: dict[str, ConstructAnchor]) -> None:
    st.markdown("#### PROVENANCE")
    st.caption(f"{item.domain_id} / {item.facet_id}")
    for anchor_id in item.anchor_ids:
        anchor = anchors[anchor_id]
        direction = "Reverse keyed" if anchor.reverse else "Forward keyed"
        st.markdown(f"**{anchor.anchor_id}** · {direction}")
        st.write(anchor.text_zh)
    st.caption(f"Prompt {item.prompt_version} · {item.model_id or 'Curated local seed'}")
    render_status(item.evidence_status)


def render_generation_stepper(active_stage: str) -> str:
    return st.radio(
        "WORKFLOW",
        STAGES,
        index=STAGES.index(active_stage),
        key="v2_generation_stepper",
    )
```

Implement each with Streamlit controls or escaped HTML. Any candidate text inserted into HTML must be passed through `html.escape`.

Every page exposes the same signature: `render(project: ResearchProject, anchors: dict[str, ConstructAnchor], service: WorkbenchService) -> None`. `app_v2.py` calls `st.set_page_config(page_title="Adolescent Big Five Workbench", page_icon="A", layout="wide", initial_sidebar_state="collapsed")`, applies the theme, initializes `JsonProjectRepository(ROOT / "workspace_data/v2/projects")`, seeds `build_demo_project()`, loads anchors with `load_anchor_asset(ANCHOR_ASSET)`, renders the custom navigation, and dispatches to the five page functions. Missing model configuration changes only the LIVE button state. At this task boundary, create working read-only baseline pages for GENERATION STUDIO, REVIEW, and PARTICIPANT VIEW: generation renders a selected seed item's four stages; review renders the five-row seed queue; participant renders the first Chinese seed item with four choices. Tasks 7 and 8 add editing, live generation, history, and multi-item navigation.

- [ ] **Step 6: Implement PROJECT**

Render a compact black project band with title, age range, locale, `CURATED DEMO` badge, and the statement `Candidate item development — empirical validation required`. Below it, render the three-stage lineage `2023 EMPIRICAL STUDY -> 2026 RECONSTRUCTION -> ADOLESCENT BEHAVIORAL PHENOTYPES`. Do not display an exact historical sample size until it is verified. Show five factual project metrics: 60 anchors, 15 facets, 5 domains, 5 curated candidates, 0 validated items.

Add a compact `ARCHIVED 2023 EVIDENCE` table with the exact slide-reported alpha/omega pairs: Conscientiousness `.750/.87`, Openness `.702/.79`, Neuroticism `.789/.85`, Extraversion `.887/.84`, and Agreeableness `.875/.82`; also show `Openness item-total r: .455-.664`. Label the block `Archived slide summary; raw participant data unavailable; not evidence for V2.` Do not recompute, reinterpret, or imply comparison with V2.

- [ ] **Step 7: Implement CONSTRUCT MAP**

Build a Plotly sunburst from the five domains and 15 facets. Use domain colors from `taxonomy.py`, black/white typography, no gradient, and hover text with English and Chinese facet labels. Pair it with a stable facet selector. The detail panel displays definition, domain, four migrated anchors, reverse-key status, and the statement `Source anchors guide content; the facet is the generation unit.`

- [ ] **Step 8: Run the AppTest smoke test**

Run: `python -m pytest tests/test_app_smoke.py -v`

Expected: pass without credentials.

- [ ] **Step 9: Commit the shell and first two views**

```powershell
git add app_v2.py psychometric_v2/assets/fonts psychometric_v2/ui tests/test_app_smoke.py
git commit -m "feat: build Alto-inspired V2 research shell"
```

## Task 7: Build GENERATION STUDIO and REVIEW

**Files:**
- Modify: `psychometric_v2/ui/pages/generation.py`
- Modify: `psychometric_v2/ui/pages/review.py`
- Modify: `app_v2.py`
- Modify: `tests/test_app_smoke.py`

- [ ] **Step 1: Add failing UI assertions for generation and review content**

Extend `tests/test_app_smoke.py` with AppTest navigation helpers. Assert that curated mode exposes `CONSTRUCT SPECIFICATION`, `SCENARIO BLUEPRINT`, `RESPONSE OPTIONS`, and `QUALITY CHECKS`; assert that REVIEW exposes exactly five candidates plus the action controls `SAVE REVISION`, `RETURN`, and `APPROVE CONTENT`; assert that GENERATION STUDIO exposes `GENERATE` and `LOAD CURATED EXAMPLE`. Set the active page through `session_state["v2_active_page"]` before `.run()` so the test does not depend on CSS selectors.

- [ ] **Step 2: Run the focused smoke tests and confirm failure**

Run: `python -m pytest tests/test_app_smoke.py -v`

Expected: failures for the editing and live-generation controls that are absent from the read-only baseline.

- [ ] **Step 3: Implement the curated generation studio**

Use a three-column grid: compact workflow rail, central stage work area, and right provenance inspector. The top controls are generation mode, domain, facet, context domain, and anchor. In `CURATED DEMO`, selecting an item loads its complete construct specification, blueprint, options, and checks without a model call. Each stage has an explicit status and can be inspected independently.

- [ ] **Step 4: Implement live staged generation**

Create the model client only after the user clicks `GENERATE`. Run one stage at a time and store validated stage objects in `v2_construct_spec`, `v2_scenario_blueprint`, and `v2_candidate_item`. On failure, show the public stage error and a `LOAD CURATED EXAMPLE` action while retaining completed stages. Label generated content `LIVE GENERATION` and store the returned candidate through `WorkbenchService` only after the option stage validates.

- [ ] **Step 5: Implement quality-check presentation**

Render deterministic checks and any model-assisted checks as a flat list with outcome, severity, evidence, and recommendation. `PASS` uses cyan, `FLAG/WARNING` uses orange, and structural errors use magenta/red. Include the fixed note `Automated checks are advisory; human review is required.`

- [ ] **Step 6: Implement the review queue and editor**

Render a compact dataframe with item ID, domain, facet, context, error/warning counts, status, and version count. A stable selectbox opens the item editor. Use one text area for the stem and four fixed-height option inputs ordered by `display_order`. Hide scores by default behind `RESEARCH METADATA`. Actions are `SAVE REVISION`, `RETURN`, `APPROVE CONTENT`, and `PROMOTE TO PILOT`; disable promotion unless the current status is `HUMAN_REVIEWED`. Require a non-empty reviewer note for every action.

- [ ] **Step 7: Implement provenance and version history**

The right panel shows source anchor text, reverse metadata, domain/facet, observable behavior rationales, model ID or `Curated local seed`, prompt version, generation timestamp, checks, and evidence status. Version history shows reviewer, action, timestamp, note, and content snapshot; it never exposes chain-of-thought.

- [ ] **Step 8: Run service and UI tests**

Run: `python -m pytest tests/test_workbench.py tests/test_app_smoke.py -v`

Expected: all pass.

- [ ] **Step 9: Commit generation and review views**

```powershell
git add app_v2.py psychometric_v2/ui/pages/generation.py psychometric_v2/ui/pages/review.py tests/test_app_smoke.py
git commit -m "feat: add staged generation and review views"
```

## Task 8: Participant Preview, Downloads, Launch Documentation, and Final Verification

**Files:**
- Modify: `psychometric_v2/ui/pages/participant.py`
- Create: `README_V2.md`
- Create: `run_v2.ps1`
- Modify: `app_v2.py`
- Modify: `tests/test_app_smoke.py`

- [ ] **Step 1: Add failing participant privacy assertions**

Extend `tests/test_app_smoke.py` to open `PARTICIPANT VIEW` and assert that Chinese stems, `1 / 5`, four response choices, and previous/next controls render while `anchor_ids`, `trait_level`, `score`, `Extraversion`, and `VALIDATED` do not appear in participant-facing markdown.

- [ ] **Step 2: Run the smoke test and confirm failure**

Run: `python -m pytest tests/test_app_smoke.py -v`

Expected: failure because the read-only baseline does not yet provide five-item progress and navigation.

- [ ] **Step 3: Implement the five-item participant preview**

Render one item at a time with fixed progress `1 / 5`, the Chinese instruction, stem, and radio choices sorted by `display_order`. Store only the selected `option_id` in `v2_participant_responses`. Provide icon-based previous/next controls with tooltips. On completion show `Preview complete` and `Responses remain in this session only`; do not calculate, display, or download a personality profile.

- [ ] **Step 4: Add research-only downloads**

Place JSON and CSV download buttons in REVIEW, not PARTICIPANT VIEW. Filenames are `adolescent_big_five_demo.json` and `adolescent_big_five_items.csv`. JSON contains complete provenance; CSV contains 20 option rows. Neither export contains participant-preview responses.

- [ ] **Step 5: Add the one-command launcher**

```powershell
# run_v2.ps1
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $repoRoot
python -m streamlit run app_v2.py --server.port 8501 --server.headless true
```

Document these exact commands in `README_V2.md`:

```powershell
python -m pip install -r requirements-v2.txt
powershell -ExecutionPolicy Bypass -File .\run_v2.ps1
python -m pytest
```

Document `OPENAI_API_KEY`, `LLM_MODEL`, and optional `OPENAI_BASE_URL`; state that no credentials are required for CURATED DEMO. Include the 6-8 minute demo sequence from the design spec and the explicit non-validation disclaimer.

- [ ] **Step 6: Run the full automated suite**

Run: `python -m pytest -v`

Expected: every test passes; no test makes a network call.

- [ ] **Step 7: Start the application and run both demo paths**

Run: `powershell -ExecutionPolicy Bypass -File .\run_v2.ps1`

Expected: Streamlit reports `Local URL: http://localhost:8501`; PROJECT loads in CURATED DEMO without credentials.

Manually complete:

1. PROJECT -> CONSTRUCT MAP -> GENERATION STUDIO with curated content.
2. Inspect all four generation stages and provenance.
3. Edit one option in REVIEW, save it, and confirm a new version appears.
4. Approve the item and confirm `HUMAN_REVIEWED`, never `VALIDATED`.
5. Complete all five items in PARTICIPANT VIEW and confirm no profile appears.
6. Download JSON/CSV and verify participant choices are absent.
7. When credentials are available, live-generate one item; otherwise verify the disabled live-state message.

- [ ] **Step 8: Perform browser visual verification**

Use the in-app browser against `http://localhost:8501` and capture PROJECT, GENERATION STUDIO, REVIEW, and PARTICIPANT VIEW at:

- 1440x900 desktop;
- 1280x720 presentation laptop;
- 390x844 participant mobile.

Verify nonblank rendering, Source Sans 3 loading, black/white band hierarchy, magenta active state, cyan provenance, orange warnings, no overlapping text, no clipped Chinese options, a usable collapsed layout at mobile width, and no layout shift between options.

- [ ] **Step 9: Fix only verification findings and rerun checks**

For each finding, add or update a focused test where practical, apply the smallest CSS/view correction, rerun `python -m pytest -v`, and repeat the affected screenshot. Do not add deferred scope such as reports, statistics, authentication, or extra constructs.

- [ ] **Step 10: Commit the presentation-ready release**

```powershell
git add app_v2.py psychometric_v2/ui/pages/participant.py README_V2.md run_v2.ps1 tests/test_app_smoke.py
git commit -m "feat: complete presentation-ready V2 workbench"
```

Run: `git status --short`

Expected: no tracked changes; the ignored legacy project and runtime workspace do not appear.

## Delivery Gate

Do not call the first stage complete until all of the following are true:

- `python -m pytest -v` passes.
- The app launches from `run_v2.ps1` without an API key.
- Five domains, 15 facets, 60 anchors, 30 reverse anchors, and five demo candidates are visible and correct.
- One item can be edited, reviewed, versioned, previewed, and exported without losing provenance.
- CURATED DEMO and LIVE GENERATION are truthfully distinguished.
- Participant preview contains no scoring or personality conclusion.
- Desktop, laptop, and participant-mobile screenshots have been inspected.
- Legacy code, ZIP, slides, logs, and data remain untouched.
