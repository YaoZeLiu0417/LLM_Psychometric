import struct
import zlib
from pathlib import Path

import pytest
from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSET_DIR = ROOT / "docs" / "assets" / "readme"


def _documentation() -> str:
    assert README.exists(), "README.md must exist at the repository root"
    return README.read_text(encoding="utf-8")


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
    required_phrases = (
        "# Adolescent Big Five Workbench",
        "https://adolescent-big-five-workbench.streamlit.app/",
        "5 domains",
        "15 facets",
        "60 traceable anchors",
        "mainland Chinese adolescents aged 12-15",
        "From 2023 to the Current Workbench",
        "college students",
        "Construct Map",
        "Generation Studio",
        "Human Review",
        "Participant View",
        "not a validated assessment",
        "executive function",
        "psychopathology-related phenotypes",
        "neuroimaging",
    )

    for phrase in required_phrases:
        assert phrase in documentation


def test_root_readme_documents_the_real_operating_contract() -> None:
    documentation = _documentation()
    required_phrases = (
        "## 中文使用说明",
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
        "Workflow / Human Review",
        "does not consume model tokens",
        "普通浏览不会调用模型，也不会消耗模型 token（does not consume model tokens）。",
        "README_V2.md",
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
    ):
        assert inaccurate_claim not in documentation


def test_root_readme_assets_are_real_consistent_png_captures() -> None:
    documentation = _documentation()
    asset_names = (
        "construct-map.png",
        "generation-studio.png",
        "review-workbench.png",
        "participant-view.png",
    )
    dimensions: set[tuple[int, int]] = set()

    for asset_name in asset_names:
        relative_path = f"docs/assets/readme/{asset_name}"
        assert relative_path in documentation
        asset_path = ASSET_DIR / asset_name
        assert asset_path.is_file(), f"Missing README asset: {asset_name}"
        width, height = _png_size(asset_path)
        assert width >= 1000
        assert height >= 650
        dimensions.add((width, height))

    assert len(dimensions) == 1, "README screenshots must share one viewport"
