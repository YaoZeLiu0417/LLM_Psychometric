import struct
import zlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSET_DIR = ROOT / "docs" / "assets" / "readme"


def _documentation() -> str:
    assert README.exists(), "README.md must exist at the repository root"
    return README.read_text(encoding="utf-8")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"

    offset = 8
    width = height = None
    idat_parts: list[bytes] = []
    saw_iend = False
    chunk_index = 0

    while offset < len(data):
        assert len(data) - offset >= 12, f"{path} is truncated"
        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + chunk_length
        chunk_end = payload_end + 4
        assert chunk_end <= len(data), f"{path} is truncated"

        payload = data[payload_start:payload_end]
        expected_crc = struct.unpack(">I", data[payload_end:chunk_end])[0]
        actual_crc = zlib.crc32(payload, zlib.crc32(chunk_type)) & 0xFFFFFFFF
        assert actual_crc == expected_crc, f"{path} has an invalid {chunk_type!r} CRC"

        if chunk_type == b"IHDR":
            assert chunk_index == 0 and width is None, f"{path} has an invalid IHDR"
            assert chunk_length == 13, f"{path} has an invalid IHDR"
            (
                width,
                height,
                bit_depth,
                color_type,
                compression_method,
                filter_method,
                interlace_method,
            ) = struct.unpack(">IIBBBBB", payload)
            valid_bit_depths = {
                0: {1, 2, 4, 8, 16},
                2: {8, 16},
                3: {1, 2, 4, 8},
                4: {8, 16},
                6: {8, 16},
            }
            assert width > 0 and height > 0, f"{path} has an invalid IHDR"
            assert bit_depth in valid_bit_depths.get(color_type, set()), (
                f"{path} has an invalid IHDR"
            )
            assert compression_method == 0, f"{path} has an invalid IHDR"
            assert filter_method == 0, f"{path} has an invalid IHDR"
            assert interlace_method in (0, 1), f"{path} has an invalid IHDR"
        elif chunk_type == b"IDAT":
            assert width is not None, f"{path} has IDAT before IHDR"
            idat_parts.append(payload)
        elif chunk_type == b"IEND":
            assert chunk_length == 0, f"{path} has an invalid IEND"
            assert width is not None, f"{path} has IEND before IHDR"
            assert idat_parts, f"{path} has no IDAT data"
            assert chunk_end == len(data), f"{path} has data after IEND"
            saw_iend = True
            offset = chunk_end
            break

        offset = chunk_end
        chunk_index += 1

    assert saw_iend, f"{path} is truncated (missing IEND)"

    decompressor = zlib.decompressobj()
    try:
        decompressor.decompress(b"".join(idat_parts))
        decompressor.flush()
    except zlib.error as exc:
        raise AssertionError(f"{path} has invalid compressed image data") from exc
    assert decompressor.eof, f"{path} has truncated compressed image data"
    assert not decompressor.unused_data, f"{path} has extra compressed image data"

    assert width is not None and height is not None
    return width, height


def test_png_size_rejects_truncated_file(tmp_path: Path) -> None:
    truncated_path = tmp_path / "truncated.png"
    truncated_path.write_bytes((ASSET_DIR / "construct-map.png").read_bytes()[:24])

    with pytest.raises(AssertionError, match="truncated"):
        _png_size(truncated_path)


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
