# Research Dossier README and v0.1.0 Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing GitHub presentation into a research dossier with a polished interface overview, a 40-second read-only walkthrough, two responsibility-aware diagrams, an English case study, an explicit use boundary, and a verified `v0.1.0 Research Preview` release.

**Architecture:** Keep the Streamlit application and its existing README visual language unchanged. Add a reproducible documentation-asset builder that composes the four real 1280x720 workbench captures into a 1600x900 overview, a 960x540 GIF, and two accessible 1600x900 SVG diagrams; then integrate those assets through minimal Markdown edits and enforce the whole release contract in `tests/test_readme.py`.

**Tech Stack:** Python 3.11+, Pillow, SVG/XML, Markdown, pytest, Git, GitHub CLI, Streamlit Community Cloud.

---

## File Map

- Modify `tests/test_readme.py`: replace the old Mermaid-only and four-image-only contracts with dossier asset, case-study, license, and evidence-boundary tests while retaining the current deployment and operating-contract tests.
- Create `scripts/build_readme_dossier_assets.py`: reproducibly compose the overview PNG, animated walkthrough GIF, construct-to-candidate SVG, and architecture SVG from the four existing real screenshots.
- Create `docs/assets/readme/workbench-overview.png`: 1600x900 Option C interface overview with Construct Map dominant and three right-rail views.
- Create `docs/assets/readme/workbench-walkthrough.gif`: 960x540, 40-second, 8-fps, read-only walkthrough under 10 MiB.
- Create `docs/assets/readme/construct-to-candidate.svg`: three-zone theory, authoring, and governance responsibility figure.
- Create `docs/assets/readme/system-architecture.svg`: four-layer implemented-system architecture figure.
- Modify `README.md`: add two top links, use the overview as the first visual, add the walkthrough, replace Mermaid with the responsibility SVG, move the detailed Construct Map screenshot into the tour, add the architecture SVG, and link `LICENSE`.
- Create `CASE_STUDY.md`: 900-1,400 word English research and engineering portfolio narrative.
- Create `LICENSE`: all-rights-reserved academic-evaluation and reference boundary.

## Task 1: Turn the Approved Design into Failing Documentation Contracts

**Files:**
- Modify: `tests/test_readme.py:1-362`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Add XML and GIF test support plus the dossier paths**

At the top of `tests/test_readme.py`, add `xml.etree.ElementTree` and `ImageSequence`, then add the new root paths and conceptual contracts. The resulting import and constant block must contain:

```python
import re
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

import pytest
from PIL import Image, ImageSequence, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CASE_STUDY = ROOT / "CASE_STUDY.md"
LICENSE = ROOT / "LICENSE"
ASSET_DIR = ROOT / "docs" / "assets" / "readme"
OVERVIEW = ASSET_DIR / "workbench-overview.png"
WALKTHROUGH = ASSET_DIR / "workbench-walkthrough.gif"
CONSTRUCT_FLOW = ASSET_DIR / "construct-to-candidate.svg"
ARCHITECTURE = ASSET_DIR / "system-architecture.svg"
PUBLIC_WORKBENCH_URL = (
    "https://adolescent-big-five-workbench-public.streamlit.app/?embedded=true"
)
OLD_WORKBENCH_URL = "https://adolescent-big-five-workbench.streamlit.app/"

EXPECTED_KEY_HEADINGS = (
    (1, "Adolescent Big Five Workbench"),
    (2, "Research proposition"),
    (2, "From 2023 to the Current Workbench"),
    (2, "35-45 second walkthrough"),
    (2, "Research workflow"),
    (2, "Workbench tour"),
    (2, "Technical foundation"),
    (2, "Current deployment boundary"),
    (2, "Research roadmap"),
    (2, "License and research use"),
    (2, "中文使用说明"),
)
EXPECTED_SCREENSHOTS = {
    "docs/assets/readme/construct-map.png": "Construct Map",
    "docs/assets/readme/generation-studio.png": "Generation Studio",
    "docs/assets/readme/review-workbench.png": "Human Review",
    "docs/assets/readme/participant-view.png": "Participant View",
}
EXPECTED_DOSSIER_ASSETS = {
    "docs/assets/readme/workbench-overview.png": "overview",
    "docs/assets/readme/workbench-walkthrough.gif": "walkthrough",
    "docs/assets/readme/construct-to-candidate.svg": "responsibility",
    "docs/assets/readme/system-architecture.svg": "architecture",
}
EXPECTED_CASE_STUDY_HEADINGS = (
    (1, "Adolescent Big Five Workbench: Research Case Study"),
    (2, "Executive Summary"),
    (2, "Research Problem"),
    (2, "From the 2023 Master's Project to the Adolescent Workbench"),
    (2, "My Role: Researcher · System Designer · Developer"),
    (2, "Construct and Item-Development Method"),
    (2, "Human-AI Responsibility Boundary"),
    (2, "System Architecture"),
    (2, "What the Current Workbench Demonstrates"),
    (2, "What Has Not Yet Been Validated"),
    (2, "Future Research Program"),
)
```

Delete `EXPECTED_MERMAID_LINES`, because the local responsibility SVG replaces Mermaid.

- [ ] **Step 2: Replace the old local-image helper with exact screenshot and dossier contracts**

Replace `_assert_local_screenshots` with the following implementation. It deliberately checks the four detailed screenshots separately so the four new dossier assets do not weaken the existing capture contract:

```python
def _assert_local_screenshots(documentation: str) -> tuple[tuple[str, str], ...]:
    screenshot_images = tuple(
        (alt_text, target)
        for alt_text, target in _markdown_images(documentation)
        if target in EXPECTED_SCREENSHOTS
    )
    assert len(screenshot_images) == len(EXPECTED_SCREENSHOTS)

    targets = tuple(target for _, target in screenshot_images)
    assert len(set(targets)) == len(targets), "README screenshot references must be unique"
    assert set(targets) == set(EXPECTED_SCREENSHOTS)

    for alt_text, target in screenshot_images:
        normalized_alt = " ".join(alt_text.split()).casefold()
        required_label = EXPECTED_SCREENSHOTS[target]
        assert required_label.casefold() in normalized_alt, (
            f"README screenshot alt text must describe {required_label}"
        )
    return screenshot_images


def _assert_dossier_assets(documentation: str) -> tuple[tuple[str, str], ...]:
    dossier_images = tuple(
        (alt_text, target)
        for alt_text, target in _markdown_images(documentation)
        if target in EXPECTED_DOSSIER_ASSETS
    )
    assert len(dossier_images) == len(EXPECTED_DOSSIER_ASSETS)
    targets = tuple(target for _, target in dossier_images)
    assert len(set(targets)) == len(targets), "Dossier asset references must be unique"
    assert set(targets) == set(EXPECTED_DOSSIER_ASSETS)
    for alt_text, target in dossier_images:
        assert EXPECTED_DOSSIER_ASSETS[target] in " ".join(alt_text.split()).casefold()
    return dossier_images
```

Delete `_assert_workflow_mermaid`. Keep `_construct_map_image_match`, because its mutation tests still protect the detailed capture.

- [ ] **Step 3: Add strict SVG, GIF, section, and word-count helpers**

Add these helpers below `_png_size`:

```python
def _section(documentation: str, heading: str) -> str:
    marker = f"## {heading}"
    start = documentation.index(marker) + len(marker)
    next_heading = documentation.find("\n## ", start)
    return documentation[start:] if next_heading == -1 else documentation[start:next_heading]


def _svg_contract(path: Path) -> tuple[ET.Element, str]:
    root = ET.parse(path).getroot()
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["viewBox"] == "0 0 1600 900"
    assert root.attrib["role"] == "img"
    labelled_by = root.attrib["aria-labelledby"].split()
    assert len(labelled_by) == 2
    title = root.find("{http://www.w3.org/2000/svg}title")
    description = root.find("{http://www.w3.org/2000/svg}desc")
    assert title is not None and title.attrib.get("id") == labelled_by[0]
    assert description is not None and description.attrib.get("id") == labelled_by[1]
    assert title.text and title.text.strip()
    assert description.text and description.text.strip()
    return root, " ".join(" ".join(root.itertext()).split())


def _gif_contract(path: Path) -> tuple[int, int]:
    assert path.stat().st_size <= 10 * 1024 * 1024
    try:
        with Image.open(path) as image:
            assert image.format == "GIF"
            assert image.size == (960, 540)
            frame_count = 0
            total_duration_ms = 0
            fallback_duration = int(image.info.get("duration", 0))
            for frame in ImageSequence.Iterator(image):
                frame.load()
                frame_count += 1
                total_duration_ms += int(frame.info.get("duration", fallback_duration))
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise AssertionError(f"{path} is not a complete decodable GIF") from exc
    assert frame_count >= 120
    assert 35_000 <= total_duration_ms <= 45_000
    return frame_count, total_duration_ms


def _english_word_count(documentation: str) -> int:
    return len(re.findall(r"\b[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*\b", documentation))
```

- [ ] **Step 4: Replace Mermaid tests and add the complete dossier test suite**

Delete `test_root_readme_has_the_exact_vertical_workflow_mermaid` and `test_workflow_mermaid_contract_rejects_layout_and_edge_mutations`. Replace `test_local_screenshot_contract_rejects_duplicate_and_extra_images` with these focused duplicate tests, because approved dossier assets are now valid additional local images:

```python
def test_local_screenshot_contract_rejects_duplicate_capture() -> None:
    addition = "![Duplicate Construct Map](docs/assets/readme/construct-map.png)"
    with pytest.raises(AssertionError):
        _assert_local_screenshots(f"{_documentation()}\n{addition}\n")


def test_dossier_asset_contract_rejects_duplicate_asset() -> None:
    addition = "![Duplicate overview](docs/assets/readme/workbench-overview.png)"
    with pytest.raises(AssertionError):
        _assert_dossier_assets(f"{_documentation()}\n{addition}\n")
```

Append these tests after the existing PNG and screenshot tests:

```python
def test_root_readme_integrates_the_research_dossier_in_the_approved_order() -> None:
    documentation = _documentation()
    _assert_dossier_assets(documentation)
    required_links = (
        '<a href="CASE_STUDY.md">English Case Study</a>',
        '<a href="https://github.com/YaoZeLiu0417/LLM_Psychometric/releases/tag/v0.1.0">v0.1.0 Research Preview</a>',
        "[full research-use boundary](LICENSE)",
    )
    for link in required_links:
        assert documentation.count(link) == 1

    ordered_targets = (
        "docs/assets/readme/workbench-overview.png",
        "docs/assets/readme/workbench-walkthrough.gif",
        "docs/assets/readme/construct-to-candidate.svg",
        "docs/assets/readme/construct-map.png",
        "docs/assets/readme/generation-studio.png",
        "docs/assets/readme/review-workbench.png",
        "docs/assets/readme/participant-view.png",
        "docs/assets/readme/system-architecture.svg",
    )
    positions = tuple(documentation.index(target) for target in ordered_targets)
    assert positions == tuple(sorted(positions))
    assert "```mermaid" not in documentation


def test_detailed_screenshots_remain_exactly_once_in_their_tour_sections() -> None:
    documentation = _documentation()
    _assert_local_screenshots(documentation)
    section_targets = {
        "1. Construct Map": "docs/assets/readme/construct-map.png",
        "2. Generation Studio": "docs/assets/readme/generation-studio.png",
        "3. Human Review": "docs/assets/readme/review-workbench.png",
        "4. Participant View": "docs/assets/readme/participant-view.png",
    }
    for heading, target in section_targets.items():
        assert documentation.count(target) == 1
        level_three = f"### {heading}"
        start = documentation.index(level_three)
        next_section = documentation.find("\n### ", start + len(level_three))
        body = documentation[start:] if next_section == -1 else documentation[start:next_section]
        assert target in body


def test_overview_png_is_complete_and_exactly_1600_by_900() -> None:
    assert _png_size(OVERVIEW) == (1600, 900)


def test_walkthrough_gif_is_complete_readable_and_within_release_budget() -> None:
    frame_count, duration_ms = _gif_contract(WALKTHROUGH)
    assert 6 <= frame_count / (duration_ms / 1000) <= 10


@pytest.mark.parametrize(
    ("path", "required_labels"),
    (
        (
            CONSTRUCT_FLOW,
            (
                "Theoretical Inputs",
                "Model-Assisted Authoring",
                "Human Governance",
                "Source anchors and scoring direction",
                "Automated structural checks",
                "PILOT_CANDIDATE",
                "EMPIRICAL VALIDATION REQUIRED",
                "MODEL PROPOSES · RESEARCHER DECIDES · DATA VALIDATE",
            ),
        ),
        (
            ARCHITECTURE,
            (
                "Streamlit Research Views",
                "Application Services",
                "Typed Research Domain",
                "Adapters and Storage",
                "Generation coordination",
                "Review history",
                "OpenAI-compatible client",
                "durable JSON repositories",
            ),
        ),
    ),
)
def test_svg_assets_are_accessible_exact_and_conceptually_complete(
    path: Path, required_labels: tuple[str, ...]
) -> None:
    _root, visible_text = _svg_contract(path)
    for label in required_labels:
        assert label in visible_text


def test_case_study_is_an_evidence_bounded_three_to_five_minute_narrative() -> None:
    assert CASE_STUDY.is_file()
    documentation = CASE_STUDY.read_text(encoding="utf-8")
    assert _markdown_headings(documentation) == EXPECTED_CASE_STUDY_HEADINGS
    assert 900 <= _english_word_count(documentation) <= 1400
    required_phrases = (
        "mainland Chinese adolescents aged 12-15",
        "2023 master's project",
        "college students",
        "construct traceability",
        "human review",
        "not a validated assessment",
        "measurement invariance",
        "executive function",
        "psychopathology-related phenotypes",
        "neuroimaging",
    )
    for phrase in required_phrases:
        assert phrase.casefold() in documentation.casefold()
    for unsupported_claim in (
        "outperforms the 2023 system",
        "the generated items are valid",
        "supports diagnosis",
        "completed neuroimaging integration",
    ):
        assert unsupported_claim not in documentation.casefold()


def test_license_states_the_all_rights_reserved_research_use_boundary() -> None:
    assert LICENSE.is_file()
    notice = LICENSE.read_text(encoding="utf-8")
    required_phrases = (
        "Copyright (c) 2026 Yaoze Liu. All rights reserved.",
        "viewing, academic evaluation, and reference only",
        "is not open-source software",
        "GitHub Terms of Service",
        "copy, modify, redistribute, sublicense",
        "host a derivative deployment",
        "empirical study",
        "Third-party questionnaire wording",
        "validated assessment",
        "diagnostic, clinical, educational placement, employment",
        "not legal advice",
    )
    for phrase in required_phrases:
        assert phrase in notice
```

- [ ] **Step 5: Run the focused tests to prove the new contract is red**

Run:

```powershell
python -m pytest tests/test_readme.py -q
```

Expected: FAIL because `workbench-overview.png`, `workbench-walkthrough.gif`, `construct-to-candidate.svg`, `system-architecture.svg`, `CASE_STUDY.md`, and `LICENSE` do not exist and the README still contains Mermaid.

- [ ] **Step 6: Commit the red contract**

```powershell
git add tests/test_readme.py
git commit -m "test: define research dossier release contract"
```

## Task 2: Build the Overview and Accessible Research Diagrams

**Files:**
- Create: `scripts/build_readme_dossier_assets.py`
- Create: `docs/assets/readme/workbench-overview.png`
- Create: `docs/assets/readme/construct-to-candidate.svg`
- Create: `docs/assets/readme/system-architecture.svg`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Create the deterministic documentation asset builder**

Create `scripts/build_readme_dossier_assets.py` with the following complete content. The builder uses only the four committed real interface captures and the committed Source Sans font; it does not call the application, a model, or the network.

```python
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets" / "readme"
FONT_PATH = ROOT / "psychometric_v2" / "assets" / "fonts" / "SourceSans3-Variable.ttf"
BLACK = "#0B0B0D"
MAGENTA = "#D81B78"
VIOLET = "#40358C"
CYAN = "#24A8D8"
ORANGE = "#EF5A24"
NEUTRAL = "#F5F5F6"
WHITE = "#FFFFFF"
MUTED = "#696A72"


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def _screenshot(name: str) -> Image.Image:
    with Image.open(ASSET_DIR / name) as image:
        return image.convert("RGB")


def _paste_capture(
    canvas: Image.Image,
    capture: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    fitted = ImageOps.fit(
        capture,
        (right - left, bottom - top),
        method=Image.Resampling.LANCZOS,
    )
    canvas.paste(fitted, (left, top))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(box, outline=BLACK, width=2)


def build_overview() -> None:
    canvas = Image.new("RGB", (1600, 900), NEUTRAL)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1600, 118), fill=BLACK)
    draw.text((48, 27), "ADOLESCENT BIG FIVE WORKBENCH", font=_font(34), fill=WHITE)
    draw.text((1110, 31), "FROM CONSTRUCT TO CANDIDATE", font=_font(22), fill=WHITE)
    draw.rectangle((1110, 72, 1552, 78), fill=MAGENTA)

    left_box = (48, 154, 1042, 846)
    _paste_capture(canvas, _screenshot("construct-map.png"), left_box)
    draw.rectangle((48, 154, 1042, 208), fill=BLACK)
    draw.text((70, 167), "01  CONSTRUCT MAP", font=_font(25), fill=WHITE)

    right_cards = (
        ("generation-studio.png", "02  GENERATION STUDIO", MAGENTA, (1070, 154, 1552, 368)),
        ("review-workbench.png", "03  HUMAN REVIEW", CYAN, (1070, 393, 1552, 607)),
        ("participant-view.png", "04  PARTICIPANT VIEW", ORANGE, (1070, 632, 1552, 846)),
    )
    for filename, label, accent, box in right_cards:
        _paste_capture(canvas, _screenshot(filename), box)
        left, top, right, _bottom = box
        draw.rectangle((left, top, right, top + 43), fill=BLACK)
        draw.rectangle((left, top, left + 8, top + 43), fill=accent)
        draw.text((left + 22, top + 9), label, font=_font(20), fill=WHITE)

    canvas.save(ASSET_DIR / "workbench-overview.png", format="PNG", optimize=True)


def _svg_document(title: str, description: str, body: str, title_id: str) -> str:
    description_id = f"{title_id}-description"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-labelledby="{title_id} {description_id}">
  <title id="{title_id}">{title}</title>
  <desc id="{description_id}">{description}</desc>
  <style>
    text {{ font-family: "Source Sans 3", Arial, sans-serif; letter-spacing: 0; }}
    .eyebrow {{ font-size: 22px; font-weight: 700; }}
    .heading {{ font-size: 36px; font-weight: 700; }}
    .label {{ font-size: 25px; font-weight: 650; }}
    .body {{ font-size: 21px; font-weight: 450; }}
    .small {{ font-size: 18px; font-weight: 600; }}
  </style>
  <rect width="1600" height="900" fill="{NEUTRAL}"/>
{body}
</svg>
'''


def build_construct_flow() -> None:
    body = f'''
  <rect x="0" y="0" width="1600" height="112" fill="{BLACK}"/>
  <text x="56" y="48" class="eyebrow" fill="{CYAN}">RESEARCH RESPONSIBILITY MAP</text>
  <text x="56" y="88" class="heading" fill="{WHITE}">From construct anchors to pilot candidates</text>

  <rect x="56" y="156" width="456" height="604" rx="4" fill="{WHITE}" stroke="{VIOLET}" stroke-width="3"/>
  <rect x="56" y="156" width="456" height="12" fill="{VIOLET}"/>
  <text x="86" y="213" class="eyebrow" fill="{VIOLET}">01 / THEORETICAL INPUTS</text>
  <text x="86" y="261" class="heading" fill="{BLACK}">Theoretical Inputs</text>
  <text x="86" y="327" class="label" fill="{BLACK}">Source anchors and scoring direction</text>
  <text x="86" y="365" class="body" fill="{MUTED}">Traceable identifiers preserve the intended</text>
  <text x="86" y="396" class="body" fill="{MUTED}">domain, facet, wording, and keying direction.</text>
  <line x1="86" y1="438" x2="482" y2="438" stroke="#D8D8DC" stroke-width="2"/>
  <text x="86" y="487" class="label" fill="{BLACK}">Construct specification</text>
  <text x="86" y="525" class="body" fill="{MUTED}">Facet definition and observable behaviors</text>
  <text x="86" y="556" class="body" fill="{MUTED}">Exclusions and potential confounds</text>
  <rect x="86" y="627" width="310" height="48" rx="4" fill="{VIOLET}"/>
  <text x="105" y="659" class="small" fill="{WHITE}">RESEARCHER-DEFINED BOUNDARY</text>

  <rect x="572" y="156" width="456" height="604" rx="4" fill="{WHITE}" stroke="{MAGENTA}" stroke-width="3"/>
  <rect x="572" y="156" width="456" height="12" fill="{MAGENTA}"/>
  <text x="602" y="213" class="eyebrow" fill="{MAGENTA}">02 / STRUCTURED PROPOSAL</text>
  <text x="602" y="261" class="heading" fill="{BLACK}">Model-Assisted Authoring</text>
  <text x="602" y="327" class="label" fill="{BLACK}">Adolescent scenario blueprint</text>
  <text x="602" y="365" class="body" fill="{MUTED}">Mainland Chinese contexts for ages 12-15</text>
  <text x="602" y="396" class="body" fill="{MUTED}">under explicit content constraints.</text>
  <line x1="602" y1="438" x2="998" y2="438" stroke="#D8D8DC" stroke-width="2"/>
  <text x="602" y="487" class="label" fill="{BLACK}">Observable response options</text>
  <text x="602" y="525" class="body" fill="{MUTED}">Four actions, hidden scores, and rationales</text>
  <text x="602" y="556" class="body" fill="{MUTED}">Automated structural checks</text>
  <rect x="602" y="627" width="260" height="48" rx="4" fill="{MAGENTA}"/>
  <text x="621" y="659" class="small" fill="{WHITE}">MODEL-GENERATED PROPOSAL</text>

  <rect x="1088" y="156" width="456" height="604" rx="4" fill="{WHITE}" stroke="{ORANGE}" stroke-width="3"/>
  <rect x="1088" y="156" width="456" height="12" fill="{ORANGE}"/>
  <text x="1118" y="213" class="eyebrow" fill="{ORANGE}">03 / ACCOUNTABLE DECISION</text>
  <text x="1118" y="261" class="heading" fill="{BLACK}">Human Governance</text>
  <text x="1118" y="327" class="label" fill="{BLACK}">Edit and inspect</text>
  <text x="1118" y="365" class="body" fill="{MUTED}">Researcher rationale, reviewer identity,</text>
  <text x="1118" y="396" class="body" fill="{MUTED}">content approval, and review history.</text>
  <line x1="1118" y1="438" x2="1514" y2="438" stroke="#D8D8DC" stroke-width="2"/>
  <text x="1118" y="487" class="label" fill="{BLACK}">PILOT_CANDIDATE</text>
  <text x="1118" y="525" class="body" fill="{MUTED}">Promotion records workflow status only.</text>
  <text x="1118" y="556" class="body" fill="{MUTED}">EMPIRICAL VALIDATION REQUIRED</text>
  <rect x="1118" y="627" width="283" height="48" rx="4" fill="{ORANGE}"/>
  <text x="1137" y="659" class="small" fill="{WHITE}">RESEARCHER-OWNED DECISION</text>

  <path d="M520 455 H557" stroke="{BLACK}" stroke-width="4"/>
  <path d="M548 445 L562 455 L548 465" fill="none" stroke="{BLACK}" stroke-width="4"/>
  <path d="M1036 455 H1073" stroke="{BLACK}" stroke-width="4"/>
  <path d="M1064 445 L1078 455 L1064 465" fill="none" stroke="{BLACK}" stroke-width="4"/>

  <rect x="0" y="812" width="1600" height="88" fill="{BLACK}"/>
  <text x="800" y="867" text-anchor="middle" class="label" fill="{WHITE}">MODEL PROPOSES &#183; RESEARCHER DECIDES &#183; DATA VALIDATE</text>
'''
    path = ASSET_DIR / "construct-to-candidate.svg"
    path.write_text(
        _svg_document(
            "Construct-to-candidate responsibility flow",
            "Three responsibility zones distinguish theoretical inputs, model-assisted authoring, and human governance before empirical validation.",
            body,
            "construct-flow-title",
        ),
        encoding="utf-8",
    )


def build_architecture() -> None:
    rows = (
        (
            154,
            CYAN,
            "01",
            "Streamlit Research Views",
            "Project   ·   Construct Map   ·   Generation   ·   Review   ·   Participant View",
        ),
        (
            312,
            MAGENTA,
            "02",
            "Application Services",
            "Workflow state   ·   Authorization   ·   Generation coordination   ·   Review transitions",
        ),
        (
            470,
            VIOLET,
            "03",
            "Typed Research Domain",
            "Anchors   ·   Specifications   ·   Candidates   ·   Quality checks   ·   Review history   ·   Evidence state",
        ),
        (
            628,
            ORANGE,
            "04",
            "Adapters and Storage",
            "OpenAI-compatible client   ·   Session-isolated and durable JSON repositories   ·   Reference exports",
        ),
    )
    row_markup = []
    for top, accent, number, heading, details in rows:
        row_markup.append(
            f'''
  <rect x="84" y="{top}" width="1432" height="124" rx="4" fill="{WHITE}" stroke="#D8D8DC" stroke-width="2"/>
  <rect x="84" y="{top}" width="14" height="124" fill="{accent}"/>
  <text x="126" y="{top + 47}" class="eyebrow" fill="{accent}">{number}</text>
  <text x="206" y="{top + 50}" class="heading" fill="{BLACK}">{heading}</text>
  <text x="206" y="{top + 91}" class="body" fill="{MUTED}">{details}</text>'''
        )
    body = f'''
  <rect x="0" y="0" width="1600" height="112" fill="{BLACK}"/>
  <text x="56" y="48" class="eyebrow" fill="{CYAN}">IMPLEMENTED SYSTEM BOUNDARIES</text>
  <text x="56" y="88" class="heading" fill="{WHITE}">Research workbench architecture</text>
  {''.join(row_markup)}
  <path d="M800 278 V304" stroke="{BLACK}" stroke-width="4"/>
  <path d="M792 295 L800 306 L808 295" fill="none" stroke="{BLACK}" stroke-width="4"/>
  <path d="M800 436 V462" stroke="{BLACK}" stroke-width="4"/>
  <path d="M792 453 L800 464 L808 453" fill="none" stroke="{BLACK}" stroke-width="4"/>
  <path d="M800 594 V620" stroke="{BLACK}" stroke-width="4"/>
  <path d="M792 611 L800 622 L808 611" fill="none" stroke="{BLACK}" stroke-width="4"/>
  <rect x="0" y="812" width="1600" height="88" fill="{BLACK}"/>
  <text x="800" y="850" text-anchor="middle" class="label" fill="{WHITE}">DOMAIN AND SERVICE BOUNDARIES SUPPORT FUTURE INTERFACES</text>
  <text x="800" y="878" text-anchor="middle" class="small" fill="#CFCFD4">No React or FastAPI implementation is claimed in this release.</text>
'''
    path = ASSET_DIR / "system-architecture.svg"
    path.write_text(
        _svg_document(
            "Adolescent Big Five Workbench system architecture",
            "Four implemented layers separate Streamlit research views, application services, typed research domain objects, and adapters and storage.",
            body,
            "architecture-title",
        ),
        encoding="utf-8",
    )


def main() -> None:
    build_overview()
    build_construct_flow()
    build_architecture()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate the overview and SVG assets**

Run:

```powershell
python scripts/build_readme_dossier_assets.py
```

Expected: the command exits 0 and creates the three declared files without modifying the four source captures.

- [ ] **Step 3: Run the focused visual contract tests**

Run:

```powershell
python -m pytest tests/test_readme.py -q -k "overview_png or svg_assets"
```

Expected: PASS.

- [ ] **Step 4: Inspect the generated visual assets at full resolution**

Open all three assets and verify: no cropped labels; Construct Map dominates the overview; Generation, Review, and Participant View form a balanced right rail; both SVGs remain legible at GitHub width; no gradients, fabricated interface controls, or overlapping text are present.

- [ ] **Step 5: Commit the reproducible visual assets**

```powershell
git add scripts/build_readme_dossier_assets.py docs/assets/readme/workbench-overview.png docs/assets/readme/construct-to-candidate.svg docs/assets/readme/system-architecture.svg
git commit -m "docs: add research dossier visual system"
```

## Task 3: Add the 40-Second Read-Only Walkthrough

**Files:**
- Modify: `scripts/build_readme_dossier_assets.py`
- Create: `docs/assets/readme/workbench-walkthrough.gif`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Add deterministic GIF composition to the asset builder**

Add the following functions immediately before `main()` in `scripts/build_readme_dossier_assets.py`:

```python
def _walkthrough_scene(
    source: Image.Image,
    eyebrow: str,
    heading: str,
    accent: str,
) -> Image.Image:
    frame = ImageOps.fit(source, (960, 540), method=Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, 960, 102), fill=(11, 11, 13, 235))
    draw.rectangle((0, 0, 10, 102), fill=accent)
    draw.text((30, 18), eyebrow, font=_font(18), fill=accent)
    draw.text((30, 46), heading, font=_font(31), fill=WHITE)
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def build_walkthrough() -> None:
    overview = _screenshot("workbench-overview.png")
    scenes = (
        _walkthrough_scene(
            overview,
            "RESEARCH PREVIEW / READ-ONLY",
            "From the 2023 college-student project to an adolescent workbench",
            CYAN,
        ),
        _walkthrough_scene(
            _screenshot("construct-map.png"),
            "01 / THEORETICAL INPUTS",
            "Inspect domains, facets, source anchors, and scoring direction",
            VIOLET,
        ),
        _walkthrough_scene(
            _screenshot("generation-studio.png"),
            "02 / MODEL-ASSISTED AUTHORING",
            "Review construct, blueprint, options, rationales, and checks",
            MAGENTA,
        ),
        _walkthrough_scene(
            _screenshot("review-workbench.png"),
            "03 / HUMAN GOVERNANCE",
            "Inspect provenance, edit content, and record review decisions",
            CYAN,
        ),
        _walkthrough_scene(
            _screenshot("participant-view.png"),
            "04 / PARTICIPANT PREVIEW",
            "Preview pilot candidates without scores or personality feedback",
            ORANGE,
        ),
    )
    frames_per_scene = 64
    total_frames = frames_per_scene * len(scenes)
    rgb_frames: list[Image.Image] = []
    for scene_index, scene in enumerate(scenes):
        previous = scenes[scene_index - 1] if scene_index else scene
        for local_index in range(frames_per_scene):
            if scene_index and local_index < 8:
                alpha = (local_index + 1) / 8
                frame = Image.blend(previous, scene, alpha)
            else:
                frame = scene.copy()
            draw = ImageDraw.Draw(frame)
            global_index = scene_index * frames_per_scene + local_index
            progress = max(1, round(960 * (global_index + 1) / total_frames))
            draw.rectangle((0, 536, 960, 540), fill=BLACK)
            draw.rectangle((0, 536, progress, 540), fill=MAGENTA)
            rgb_frames.append(frame)

    palette = rgb_frames[0].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    gif_frames = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in rgb_frames
    ]
    gif_frames[0].save(
        ASSET_DIR / "workbench-walkthrough.gif",
        format="GIF",
        save_all=True,
        append_images=gif_frames[1:],
        duration=125,
        loop=0,
        disposal=2,
        optimize=True,
    )
```

Update `main()` to call all four builders in this exact order:

```python
def main() -> None:
    build_overview()
    build_construct_flow()
    build_architecture()
    build_walkthrough()
```

- [ ] **Step 2: Generate the GIF and run its strict contract**

Run:

```powershell
python scripts/build_readme_dossier_assets.py
python -m pytest tests/test_readme.py -q -k walkthrough_gif
```

Expected: PASS with a 960x540 GIF, 320 decoded frames, 40,000 ms duration, 8 fps, and size no greater than 10 MiB.

- [ ] **Step 3: Visually inspect the full loop**

Play `docs/assets/readme/workbench-walkthrough.gif` from beginning to end. Verify readable pauses, clean scene changes, a stable progress indicator, no credentials or access codes, no Generate click, no claim that a reference item was generated during recording, and no path or personal information.

- [ ] **Step 4: Commit the walkthrough**

```powershell
git add scripts/build_readme_dossier_assets.py docs/assets/readme/workbench-walkthrough.gif
git commit -m "docs: add read-only workbench walkthrough"
```

## Task 4: Integrate the Dossier Assets into the Existing README

**Files:**
- Modify: `README.md:7-123`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Add the case-study and release links without changing the existing top layout**

Replace the centered link paragraph with:

```html
<p>
  <a href="https://adolescent-big-five-workbench-public.streamlit.app/?embedded=true">Open the deployed app</a>
  · <a href="#research-workflow">Research workflow</a>
  · <a href="CASE_STUDY.md">English Case Study</a>
  · <a href="https://github.com/YaoZeLiu0417/LLM_Psychometric/releases/tag/v0.1.0">v0.1.0 Research Preview</a>
  · <a href="#中文使用说明">中文使用说明</a>
</p>
```

- [ ] **Step 2: Replace only the first visual with the composite overview**

Replace the top Construct Map image with:

```markdown
![Adolescent Big Five Workbench interface overview with a dominant Construct Map and a right rail for generation, human review, and participant preview](docs/assets/readme/workbench-overview.png)
```

- [ ] **Step 3: Add the short walkthrough after project lineage**

Insert this complete section between `From 2023 to the Current Workbench` and `Research workflow`:

```markdown
## 35-45 second walkthrough

![Read-only walkthrough of the research workbench from construct overview through generation, responsibility review, and participant preview](docs/assets/readme/workbench-walkthrough.gif)

The walkthrough uses the same reference content available in the public read-only deployment. It does not press Generate, call a model, or present the displayed candidates as psychometrically validated items.
```

- [ ] **Step 4: Replace the Mermaid block with the responsibility-zoned SVG**

Replace the complete Mermaid fenced block under `## Research workflow` with:

```markdown
![Construct-to-candidate responsibility flow separating theoretical inputs, model-assisted authoring, and human governance before empirical validation](docs/assets/readme/construct-to-candidate.svg)
```

Retain the explanatory paragraph that follows the old Mermaid block exactly.

- [ ] **Step 5: Restore the detailed Construct Map screenshot inside its tour subsection**

Immediately below `### 1. Construct Map`, insert:

```markdown
![Construct Map showing Big Five domains, facets, source identifiers, direction, and anchor-linked traceability](docs/assets/readme/construct-map.png)
```

Keep the existing Construct Map paragraph after the image. Do not duplicate any of the other three detailed screenshots.

- [ ] **Step 6: Add the architecture figure inside Technical foundation**

Immediately below `## Technical foundation`, before the existing table or prose, insert:

```markdown
![System architecture showing Streamlit research views, application services, the typed research domain, and adapters and storage](docs/assets/readme/system-architecture.svg)
```

- [ ] **Step 7: Replace the license summary with an explicit link-level boundary**

Replace the existing two-sentence `License and research use` paragraph with:

```markdown
This public repository is available for viewing, academic evaluation, and reference, but it is not open-source software and does not grant unrestricted reuse. Copying, modification, redistribution, derivative deployment, or empirical use requires prior written permission; third-party materials retain their own rights and terms. See the [full research-use boundary](LICENSE).
```

- [ ] **Step 8: Run README integration tests**

Run:

```powershell
python -m pytest tests/test_readme.py -q -k "root_readme or detailed_screenshots"
```

Expected: all selected README integration, operating-contract, link, and screenshot tests pass; case-study and license tests remain red until Task 5.

- [ ] **Step 9: Commit the minimal README integration**

```powershell
git add README.md
git commit -m "docs: integrate research dossier assets"
```

## Task 5: Publish the English Case Study and Research-Use Boundary

**Files:**
- Create: `CASE_STUDY.md`
- Create: `LICENSE`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Create the complete English case study**

Create `CASE_STUDY.md` with exactly the following content:

```markdown
# Adolescent Big Five Workbench: Research Case Study

> A research and engineering case study of a traceable, human-governed workflow for developing situational judgement item candidates for mainland Chinese adolescents aged 12-15.

![Adolescent Big Five Workbench interface overview with a dominant Construct Map and a right rail for generation, human review, and participant preview](docs/assets/readme/workbench-overview.png)

## Executive Summary

The Adolescent Big Five Workbench is a research prototype for translating established personality construct anchors into inspectable situational judgement item candidates. It was built to address a methodological and engineering question: how can a researcher use a large language model for structured item authoring without allowing the model to silently redefine the construct, erase source provenance, or substitute generated text for psychometric evidence?

The workbench makes that responsibility chain visible. A researcher selects a Big Five domain and facet, inspects traceable source anchors and their scoring direction, defines adolescent-specific behavioral boundaries, reviews a structured scenario and four observable response options, and records a human decision before a candidate can enter pilot status. The public deployment is read-only. It demonstrates the implemented workflow without exposing model credentials or consuming model tokens during anonymous browsing. The current system is not a validated assessment.

## Research Problem

Classic personality questionnaires commonly ask people to endorse decontextualized self-descriptive statements. For early adolescents, concrete situations may be easier to interpret and closer to everyday behavior, but changing the response format creates new scientific risks. A plausible scenario can still target the wrong trait. An option can sound natural while mixing the focal facet with social desirability, language ability, compliance, school achievement, or another confound. A polished interface can also make provisional content appear more mature than its evidence warrants.

The core problem is therefore not simply generating better-sounding questions. It is preserving construct intent while making every transformation inspectable: source anchor to construct specification, specification to scenario blueprint, blueprint to response options, automated checks to human review, and approved content to a clearly provisional pilot candidate. Reliability, factor structure, convergent and discriminant validity, differential item functioning, and measurement invariance remain empirical questions for later studies.

## From the 2023 Master's Project to the Adolescent Workbench

My 2023 master's project explored a related item-generation system for college students. That first version established the research direction but reflected the model capabilities and rapid-development constraints of its time. The original participant-level dataset is no longer available, so the present project does not claim a retrospective comparison, reproduce unverified sample results, or claim superiority over the 2023 system.

The reconstruction changes the target population to mainland Chinese adolescents aged 12-15 and treats the earlier project as lineage rather than validation evidence. It retains the useful idea of converting personality content into situations, but rebuilds the workflow around explicit construct traceability, typed records, staged authoring, automated structural checks, review history, deployment boundaries, and a participant-facing preview that withholds scores and personality interpretations.

## My Role: Researcher · System Designer · Developer

I defined the research framing, translated the item-development logic into a system architecture, designed the human-AI responsibility boundary, implemented the workbench, and prepared the public research preview. This combined role required decisions at three levels.

As a researcher, I specified what information must remain traceable and where empirical evidence is still missing. As a system designer, I separated research views, workflow services, typed domain records, model adapters, and storage. As a developer, I implemented the Streamlit interface, validation models, staged generation pipeline, review transitions, reference exports, public-demo protections, and automated tests. The result is intended to demonstrate methodological judgment as much as software execution.

## Construct and Item-Development Method

The facet is the authoring unit. The Construct Map organizes five domains, 15 facets, and 60 source anchors. Each anchor preserves an identifier, wording, domain, facet, and forward or reverse scoring direction. A generation request is therefore anchored to inspectable source material rather than an unconstrained personality label.

The workflow then builds a construct specification containing a Chinese definition, observable behavioral indicators, exclusions, and potential confounds. Model-assisted stages propose an adolescent scenario blueprint, four behaviorally distinct response options, hidden score ordering, and rationales. Typed schemas and quality checks reject malformed structures, duplicated options, invalid score patterns, damaged provenance, and other contract violations. These checks improve workflow discipline; they do not establish that an item measures the intended trait.

![Construct-to-candidate responsibility flow separating theoretical inputs, model-assisted authoring, and human governance before empirical validation](docs/assets/readme/construct-to-candidate.svg)

## Human-AI Responsibility Boundary

The model proposes; the researcher decides; data validate. That sentence is the governing principle of the workbench. The model may help draft definitions, scenarios, and response structures under explicit constraints. It cannot determine whether a construct interpretation is theoretically defensible, whether an adolescent context is ethically appropriate, or whether a candidate should be used in a study.

Human Review exposes the candidate's provenance, quality findings, editable Chinese content, reviewer identity, and review note. Content approval and promotion to `PILOT_CANDIDATE` are separate actions. Promotion records a workflow state, not a reliability or validity result. This separation is designed to prevent convenient software transitions from being mistaken for scientific evidence.

## System Architecture

The implementation uses four boundaries. Streamlit Research Views provide Project, Construct Map, Generation, Review, and Participant View. Application Services coordinate authorization, generation stages, workflow state, and review transitions. A Typed Research Domain represents anchors, construct specifications, candidates, quality checks, review history, and evidence state. Adapters connect the domain to an OpenAI-compatible client, session-isolated or durable JSON repositories, and reference-only exports.

![System architecture showing Streamlit research views, application services, the typed research domain, and adapters and storage](docs/assets/readme/system-architecture.svg)

These boundaries keep research rules outside page rendering and make another interface technically possible later. React and FastAPI are not implemented capabilities in this release.

## What the Current Workbench Demonstrates

The current workbench demonstrates an end-to-end, tested authoring workflow: construct selection, anchor-linked provenance, structured generation stages, schema validation, quality checks, explicit human review, pilot-state promotion, and participant preview. It also demonstrates operational judgment. Anonymous visitors can inspect reference content without model access; secrets remain outside version control; public-demo records are session-isolated; and the repository includes a history-aware public-release audit.

For a doctoral or job-talk discussion, the project provides a concrete artifact through which to examine research questions, design choices, failure modes, and future studies. It shows how psychological theory, responsible model use, and software architecture can be developed together rather than presented as separate claims.

## What Has Not Yet Been Validated

No claim is made that the candidate items are reliable, valid, age-invariant, culturally invariant, or superior to established questionnaires. The current repository does not contain a completed adolescent pilot dataset, normative scores, diagnostic thresholds, clinical interpretations, or evidence for individual-level feedback. It does not support diagnosis, educational placement, employment decisions, or other high-stakes use.

The reference items illustrate workflow behavior only. Before empirical use, the content requires expert review, cognitive interviewing with adolescents, ethics approval, pilot administration, item analysis, factor-structure testing, convergent and discriminant validation, fairness analysis, and measurement invariance assessment across relevant groups.

## Future Research Program

The immediate next step is a governed adolescent item-development study: expert content review, cognitive interviews, preregistered pilot testing, and iterative item revision based on both qualitative evidence and psychometric results. A subsequent program could compare situational and classic self-report formats, examine response processes, and evaluate whether the format adds useful behavioral information without introducing avoidable construct-irrelevant variance.

The workbench can also become a broader tool chain for adolescent individual-difference research. Prospective modules may address executive function and psychopathology-related phenotypes while preserving the same traceability and evidence-state principles. Longer-term studies could connect carefully validated behavioral measures with longitudinal or neuroimaging research. These are future research directions, not completed integrations or present capabilities.
```

- [ ] **Step 2: Create the complete all-rights-reserved notice**

Create `LICENSE` with exactly the following content:

```text
Copyright (c) 2026 Yaoze Liu. All rights reserved.

RESEARCH PREVIEW USE NOTICE

This repository and its original contents are made publicly visible for viewing, academic evaluation, and reference only. This repository is not open-source software, and public visibility does not grant a general license to reuse its contents.

Except for the limited platform rights required under the GitHub Terms of Service to host, display, view, and fork a public repository within GitHub, no permission or license is granted to copy, modify, redistribute, sublicense, sell, commercially exploit, host a derivative deployment, or incorporate this repository or its original contents into another product, service, dataset, or instrument. Use in an empirical study also requires prior written permission from the copyright holder, in addition to all applicable ethics review, participant safeguards, expert review, and psychometric validation.

Third-party questionnaire wording, construct materials, fonts, trademarks, and other third-party assets remain the property of their respective owners and are subject to their respective licenses, permissions, and terms. Nothing in this notice grants rights in those third-party materials.

Candidate items, reference content, workflow states, and software presentation do not constitute a validated assessment. No diagnostic, clinical, educational placement, employment, personality-reporting, or other high-stakes use is authorized.

For permission requests, contact the repository owner through the public repository profile.

This notice describes the project's intended use boundary and is not legal advice.
```

- [ ] **Step 3: Run the complete documentation contract**

Run:

```powershell
python -m pytest tests/test_readme.py -q
```

Expected: PASS.

- [ ] **Step 4: Confirm the case-study length and unsupported-claim boundary**

Run:

```powershell
python -c "import re; from pathlib import Path; text=Path('CASE_STUDY.md').read_text(encoding='utf-8'); print(len(re.findall(r'\b[A-Za-z0-9]+(?:[\x27-][A-Za-z0-9]+)*\b', text)))"
rg -ni "outperforms the 2023 system|the generated items are valid|supports diagnosis|completed neuroimaging integration" README.md CASE_STUDY.md
```

Expected: the word-count command prints a number from 900 through 1,400; `rg` exits 1 with no matches.

- [ ] **Step 5: Commit the case study and use boundary**

```powershell
git add CASE_STUDY.md LICENSE
git commit -m "docs: publish case study and research use boundary"
```

## Task 6: Final Review, Merge, Public Verification, and v0.1.0 Release

**Files:**
- Verify: `README.md`
- Verify: `CASE_STUDY.md`
- Verify: `LICENSE`
- Verify: `docs/assets/readme/*`
- Verify: `scripts/build_readme_dossier_assets.py`
- Verify: `tests/test_readme.py`

- [ ] **Step 1: Prove asset generation is reproducible**

Run the builder twice and verify the second run leaves no diff:

```powershell
python scripts/build_readme_dossier_assets.py
git status --short
python scripts/build_readme_dossier_assets.py
git diff --exit-code -- docs/assets/readme scripts/build_readme_dossier_assets.py
```

Expected: no tracked visual or builder diff. If GIF metadata makes this nondeterministic, fix the builder before proceeding; do not waive this gate.

- [ ] **Step 2: Run all automated release gates on the feature branch**

```powershell
python -m pytest -q
python scripts/audit_public_release.py
git diff --check master...HEAD
git status --short
```

Expected: `340+ passed, 1 skipped` with no failures; `Public release audit passed.`; no whitespace errors; clean worktree.

- [ ] **Step 3: Perform visual QA at desktop and narrow GitHub widths**

Inspect the rendered README and case study at normal desktop width and approximately 390px width. Verify the current aesthetic remains intact, the first visual is the Option C overview, all diagram text fits, the GIF loops and stays readable, detailed screenshots appear exactly once in the correct tour sections, and no text or media overlaps.

- [ ] **Step 4: Perform a final specification and code-quality review**

Review the branch against `docs/superpowers/specs/2026-07-25-readme-research-dossier-release-design.md`. Confirm every in-scope item is present, every out-of-scope boundary is respected, no application/runtime/deployment behavior changed, and all reviewer findings are resolved before integration.

- [ ] **Step 5: Merge the reviewed documentation branch into master**

From `D:\LLM_Psychometric`, fast-forward or merge the reviewed branch using the repository's current integration policy, then verify the exact merge commit:

```powershell
git switch master
git pull --ff-only origin master
git merge --no-ff codex/readme-research-dossier-design -m "merge: publish research dossier preview"
python -m pytest -q
python scripts/audit_public_release.py
git diff --check HEAD^
git status --short
```

Expected: full suite passes, public audit passes, diff check is clean, and master has no uncommitted files.

- [ ] **Step 6: Push master and verify the public deployment anonymously**

```powershell
git push origin master
```

Open `https://adolescent-big-five-workbench-public.streamlit.app/?embedded=true` in an anonymous browser session. Verify it opens without GitHub authentication, exposes the five read-only views, does not expose model configuration, and cannot construct a model client for anonymous browsing. Do not use the root URL without `?embedded=true` as the release link.

- [ ] **Step 7: Create the immutable Research Preview tag and release**

First confirm the tag and release do not already exist:

```powershell
git tag --list v0.1.0
gh release view v0.1.0
```

Expected before first publication: no local tag and `gh release view` reports that the release is not found. Then create the annotated tag at the verified master commit, push it, and create the GitHub Release:

```powershell
git tag -a v0.1.0 -m "Adolescent Big Five Workbench v0.1.0 Research Preview"
git push origin v0.1.0
$releaseNotes = @'
## Research preview

The Adolescent Big Five Workbench explores a traceable, human-reviewed workflow for transforming established Big Five anchors into situational judgement item candidates for mainland Chinese adolescents aged 12-15.

### Included in v0.1.0

- Five implemented views: Project, Construct Map, Generation Studio, Human Review, and Participant View.
- Traceable source anchors and scoring direction, staged model-assisted authoring, automated structural checks, documented human review, and participant preview.
- A public read-only deployment: https://adolescent-big-five-workbench-public.streamlit.app/?embedded=true
- A research dossier with an interface overview, a 40-second walkthrough, responsibility and architecture diagrams, and an English case study.
- Automated repository tests and a history-aware public-release audit.

### Run locally

```powershell
python -m pip install -r requirements-v2.txt
powershell -ExecutionPolicy Bypass -File .\run_v2.ps1
```

Model-assisted generation additionally requires maintainer-provided `OPENAI_API_KEY`, `LLM_MODEL`, and `LIVE_ACCESS_CODE` configuration. Anonymous browsing does not consume model tokens.

### Evidence and deployment boundaries

This is a software research preview, not a validated assessment. Candidate items still require expert review, cognitive interviewing, pilot data, reliability and validity analysis, fairness testing, and measurement invariance evaluation. Public Streamlit storage is ephemeral; review downloads contain reference items only; no diagnostic, clinical, educational-placement, employment, or other high-stakes use is authorized.

Copyright (c) 2026 Yaoze Liu. All rights reserved. The public source is available for viewing, academic evaluation, and reference only; see `LICENSE` for the full boundary.
'@
gh release create v0.1.0 --title "Adolescent Big Five Workbench v0.1.0 Research Preview" --notes $releaseNotes --verify-tag
```

No binary asset is attached; GitHub-generated source archives are the release artifacts.

- [ ] **Step 8: Verify the published release and final public links**

```powershell
gh release view v0.1.0 --json name,tagName,isDraft,isPrerelease,url,targetCommitish
git rev-list -n 1 v0.1.0
git rev-parse origin/master
```

Expected: title is `Adolescent Big Five Workbench v0.1.0 Research Preview`; tag is `v0.1.0`; draft and prerelease are false; tag commit equals `origin/master`; the README release link, case-study link, all local assets, release page, and deployed workbench URL all resolve publicly.

---

## Completion Checklist

- [ ] Existing README aesthetic, prose, badges, metrics, warnings, roadmap, and Chinese guide are preserved except for the approved small insertions.
- [ ] Construct Map is dominant in the overview; Generation, Review, and Participant View form the right rail.
- [ ] GIF is 960x540, 35-45 seconds, 6-10 fps, at least 120 frames, and no larger than 10 MiB.
- [ ] Both SVGs use `viewBox="0 0 1600 900"`, accessible titles/descriptions, stable system fonts, and readable conceptual labels.
- [ ] The responsibility footer says `MODEL PROPOSES · RESEARCHER DECIDES · DATA VALIDATE`.
- [ ] `CASE_STUDY.md` is 900-1,400 English words and contains no fabricated results or validation claims.
- [ ] `LICENSE` states the all-rights-reserved, GitHub platform-rights, third-party-rights, empirical-use, and high-stakes-use boundaries.
- [ ] No application behavior, API credentials, Streamlit secrets, deployment mode, or runtime dependency changed.
- [ ] Full tests, release audit, diff check, visual QA, anonymous deployment check, tag, and GitHub Release all pass.
