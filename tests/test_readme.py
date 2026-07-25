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

FENCED_BLOCK_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^\n]*)\n"
    r"(?P<body>.*?)^[ \t]*(?P=fence)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
MARKDOWN_IMAGE_RE = re.compile(
    r"!\[([^\]\r\n]*)\]\(\s*([^\s)]+)(?:\s+[^)\r\n]*)?\)"
)


def _documentation() -> str:
    assert README.exists(), "README.md must exist at the repository root"
    return README.read_text(encoding="utf-8")


def _markdown_headings(documentation: str) -> tuple[tuple[int, str], ...]:
    without_fences = FENCED_BLOCK_RE.sub("", documentation)
    headings: list[tuple[int, str]] = []
    for match in re.finditer(
        r"^(#{1,6})[ \t]+(.+?)[ \t]*$", without_fences, re.MULTILINE
    ):
        title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
        headings.append((len(match.group(1)), title))
    return tuple(headings)


def _assert_key_heading_order(documentation: str) -> None:
    key_titles = {title for _, title in EXPECTED_KEY_HEADINGS}
    actual = tuple(
        heading for heading in _markdown_headings(documentation) if heading[1] in key_titles
    )
    assert actual == EXPECTED_KEY_HEADINGS


def _assert_deployment_links(documentation: str) -> None:
    english_targets = re.findall(
        r'<a\s+href="([^"]+)">Open the deployed app</a>', documentation
    )
    chinese_targets = re.findall(r"\[在线工作台\]\(([^)]+)\)", documentation)

    assert english_targets == [PUBLIC_WORKBENCH_URL]
    assert chinese_targets == [PUBLIC_WORKBENCH_URL]


def _markdown_images(documentation: str) -> tuple[tuple[str, str], ...]:
    without_fences = FENCED_BLOCK_RE.sub("", documentation)
    return tuple(MARKDOWN_IMAGE_RE.findall(without_fences))


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


def _construct_map_image_match(documentation: str) -> re.Match[str]:
    return next(
        match
        for match in MARKDOWN_IMAGE_RE.finditer(documentation)
        if match.group(2) == "docs/assets/readme/construct-map.png"
    )


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(payload, zlib.crc32(chunk_type)) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", checksum)


def _png_size(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            assert image.format == "PNG"
            image.verify()
        with Image.open(path) as image:
            assert image.format == "PNG"
            image.load()
            return image.size
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, AssertionError) as exc:
        raise AssertionError(
            f"{path} is truncated or otherwise not a complete decodable PNG"
        ) from exc


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


def test_png_size_rejects_truncated_file(tmp_path: Path) -> None:
    truncated_path = tmp_path / "truncated.png"
    truncated_path.write_bytes((ASSET_DIR / "construct-map.png").read_bytes()[:24])

    with pytest.raises(AssertionError, match="truncated"):
        _png_size(truncated_path)


def test_png_size_rejects_missing_pixel_rows(tmp_path: Path) -> None:
    incomplete_path = tmp_path / "missing-pixel-rows.png"
    ihdr = struct.pack(">IIBBBBB", 1280, 720, 8, 2, 0, 0, 0)
    incomplete_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(b""))
        + _png_chunk(b"IEND", b"")
    )

    with pytest.raises(AssertionError, match="complete decodable PNG"):
        _png_size(incomplete_path)


def test_root_readme_presents_the_research_dossier() -> None:
    documentation = _documentation()
    _assert_key_heading_order(documentation)
    _assert_deployment_links(documentation)
    required_phrases = (
        "5 domains",
        "15 facets",
        "60 traceable anchors",
        "mainland Chinese adolescents aged 12-15",
        "college students",
        "not a validated assessment",
        "executive function",
        "psychopathology-related phenotypes",
        "neuroimaging",
    )

    for phrase in required_phrases:
        assert phrase in documentation



@pytest.mark.parametrize(
    "link_markup",
    (
        f'<a href="{PUBLIC_WORKBENCH_URL}">Open the deployed app</a>',
        f"[在线工作台]({PUBLIC_WORKBENCH_URL})",
    ),
)
def test_deployment_link_contract_rejects_each_mutated_target(
    link_markup: str,
) -> None:
    documentation = _documentation()
    assert link_markup in documentation

    with pytest.raises(AssertionError):
        _assert_deployment_links(
            documentation.replace(
                link_markup,
                link_markup.replace(PUBLIC_WORKBENCH_URL, "https://example.invalid/"),
                1,
            )
        )


def test_deployment_link_contract_allows_old_url_in_unrelated_prose() -> None:
    documentation = f"{_documentation()}\nHistorical endpoint: {OLD_WORKBENCH_URL}\n"

    _assert_deployment_links(documentation)


def test_root_readme_documents_the_real_operating_contract() -> None:
    documentation = _documentation()
    required_phrases = (
        "APPROVE CONTENT",
        "PROMOTE TO PILOT",
        "PILOT_CANDIDATE",
        "OPENAI_API_KEY",
        "LLM_MODEL",
        "OPENAI_BASE_URL",
        "LIVE_ACCESS_CODE",
        "python -m pip install -r requirements-v2.txt",
        "powershell -ExecutionPolicy Bypass -File .\\run_v2.ps1",
        "http://localhost:8501",
        "Streamlit Community Cloud",
        "ephemeral",
        "reference items only",
        "not live-generated candidates, even after review or promotion",
        "workspace_data/v2/projects/",
        "model identifier, prompt version, and constraint snapshot",
        "one repair attempt for schema-invalid JSON objects",
        "Workflow / Human Review",
        "does not consume model tokens",
        "普通浏览不会调用模型，也不会消耗模型 token（does not consume model tokens）。",
        "README_V2.md",
        "WORKBENCH_DEPLOYMENT",
        "public_demo",
        "research",
        "three generation attempts per session",
        "Researcher Access",
        "session-isolated",
        "anonymous browsing does not consume model tokens",
    )

    for phrase in required_phrases:
        assert phrase in documentation

    lowercase_documentation = documentation.lower()
    for unsupported_claim in ("curated demo", "live available", "408 participants"):
        assert unsupported_claim not in lowercase_documentation

    for inaccurate_claim in (
        'G --> I["JSON / CSV export"]',
        "preserves the model, prompt, and constraints",
        "source provenance",
        "Evidence / Human Reviewed",
        "including reviewed or promoted candidates",
        "not live-generated, reviewed, or promoted candidates",
        "one repair attempt for invalid structured output",
    ):
        assert inaccurate_claim not in documentation


def test_root_readme_uses_exact_local_screenshot_markdown() -> None:
    _assert_local_screenshots(_documentation())


def test_local_screenshot_contract_rejects_duplicate_capture() -> None:
    addition = "![Duplicate Construct Map](docs/assets/readme/construct-map.png)"
    with pytest.raises(AssertionError):
        _assert_local_screenshots(f"{_documentation()}\n{addition}\n")


def test_dossier_asset_contract_rejects_duplicate_asset() -> None:
    addition = "![Duplicate overview](docs/assets/readme/workbench-overview.png)"
    with pytest.raises(AssertionError):
        _assert_dossier_assets(f"{_documentation()}\n{addition}\n")


def test_local_screenshot_contract_rejects_prose_only_path() -> None:
    documentation = _documentation()
    match = _construct_map_image_match(documentation)
    prose_only = (
        documentation[: match.start()] + match.group(2) + documentation[match.end() :]
    )

    with pytest.raises(AssertionError):
        _assert_local_screenshots(prose_only)


def test_local_screenshot_contract_requires_meaningful_alt_text() -> None:
    documentation = _documentation()
    match = _construct_map_image_match(documentation)
    empty_alt = (
        documentation[: match.start()]
        + f"![]({match.group(2)})"
        + documentation[match.end() :]
    )

    with pytest.raises(AssertionError):
        _assert_local_screenshots(empty_alt)


def test_root_readme_assets_are_real_consistent_png_captures() -> None:
    documentation = _documentation()
    local_screenshots = _assert_local_screenshots(documentation)
    dimensions: set[tuple[int, int]] = set()

    for _, relative_path in local_screenshots:
        asset_path = ROOT / relative_path
        assert asset_path.is_file(), f"Missing README asset: {relative_path}"
        width, height = _png_size(asset_path)
        assert width >= 1000
        assert height >= 650
        dimensions.add((width, height))

    assert len(dimensions) == 1, "README screenshots must share one viewport"


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
