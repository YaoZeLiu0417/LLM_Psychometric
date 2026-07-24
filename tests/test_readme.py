import re
import struct
import zlib
from pathlib import Path

import pytest
from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSET_DIR = ROOT / "docs" / "assets" / "readme"

EXPECTED_KEY_HEADINGS = (
    (1, "Adolescent Big Five Workbench"),
    (2, "Research proposition"),
    (2, "From 2023 to the Current Workbench"),
    (2, "Research workflow"),
    (2, "Workbench tour"),
    (2, "Technical foundation"),
    (2, "Current deployment boundary"),
    (2, "Research roadmap"),
    (2, "License and research use"),
    (2, "中文使用说明"),
)
EXPECTED_MERMAID_LINES = (
    "flowchart TB",
    'A["Big Five source anchors"] --> B["Construct Map"]',
    'B --> C["Adolescent constraints"]',
    'C --> D["Structured generation"]',
    'D --> E["Quality checks"]',
    'E --> F["Human Review"]',
    'F --> G["PILOT_CANDIDATE"]',
    'G --> H["Participant View"]',
)
EXPECTED_SCREENSHOTS = {
    "docs/assets/readme/construct-map.png": "Construct Map",
    "docs/assets/readme/generation-studio.png": "Generation Studio",
    "docs/assets/readme/review-workbench.png": "Human Review",
    "docs/assets/readme/participant-view.png": "Participant View",
}

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


def _assert_workflow_mermaid(documentation: str) -> None:
    mermaid_blocks = tuple(
        match.group("body")
        for match in FENCED_BLOCK_RE.finditer(documentation)
        if match.group("info").strip().casefold() == "mermaid"
    )
    assert len(mermaid_blocks) == 1, "README must contain exactly one Mermaid block"
    lines = tuple(line.strip() for line in mermaid_blocks[0].splitlines() if line.strip())
    assert lines == EXPECTED_MERMAID_LINES


def _markdown_images(documentation: str) -> tuple[tuple[str, str], ...]:
    without_fences = FENCED_BLOCK_RE.sub("", documentation)
    return tuple(MARKDOWN_IMAGE_RE.findall(without_fences))


def _assert_local_screenshots(documentation: str) -> tuple[tuple[str, str], ...]:
    images = _markdown_images(documentation)
    local_images = tuple(
        (alt_text, target)
        for alt_text, target in images
        if not re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", target, re.IGNORECASE)
    )
    assert len(local_images) == len(EXPECTED_SCREENSHOTS)

    targets = tuple(target for _, target in local_images)
    assert len(set(targets)) == len(targets), "README screenshot references must be unique"
    assert set(targets) == set(EXPECTED_SCREENSHOTS)

    for alt_text, target in local_images:
        normalized_alt = " ".join(alt_text.split()).casefold()
        required_label = EXPECTED_SCREENSHOTS[target]
        assert required_label.casefold() in normalized_alt, (
            f"README screenshot alt text must describe {required_label}"
        )
    return local_images


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
    required_phrases = (
        "https://adolescent-big-five-workbench-public.streamlit.app/?embedded=true",
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

    assert "https://adolescent-big-five-workbench.streamlit.app/" not in documentation


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


def test_root_readme_has_the_exact_vertical_workflow_mermaid() -> None:
    _assert_workflow_mermaid(_documentation())


@pytest.mark.parametrize(
    ("original", "mutation"),
    (
        ("flowchart TB", "flowchart LR"),
        (
            'B --> C["Adolescent constraints"]',
            'C --> B["Adolescent constraints"]',
        ),
        ('D --> E["Quality checks"]', ""),
    ),
)
def test_workflow_mermaid_contract_rejects_layout_and_edge_mutations(
    original: str,
    mutation: str,
) -> None:
    documentation = _documentation()
    assert original in documentation

    with pytest.raises(AssertionError):
        _assert_workflow_mermaid(documentation.replace(original, mutation, 1))


def test_root_readme_uses_exact_local_screenshot_markdown() -> None:
    _assert_local_screenshots(_documentation())


@pytest.mark.parametrize(
    "addition",
    (
        "![Duplicate Construct Map](docs/assets/readme/construct-map.png)",
        "![Extra screenshot](docs/assets/readme/extra.png)",
    ),
)
def test_local_screenshot_contract_rejects_duplicate_and_extra_images(
    addition: str,
) -> None:
    with pytest.raises(AssertionError):
        _assert_local_screenshots(f"{_documentation()}\n{addition}\n")


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
