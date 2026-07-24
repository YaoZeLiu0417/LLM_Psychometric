import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSET_DIR = ROOT / "docs" / "assets" / "readme"


def _documentation() -> str:
    assert README.exists(), "README.md must exist at the repository root"
    return README.read_text(encoding="utf-8")


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert len(header) == 24, f"{path} does not contain a complete PNG header"
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    assert header[12:16] == b"IHDR", f"{path} has no IHDR chunk"
    return struct.unpack(">II", header[16:24])


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
        "does not consume model tokens",
        "README_V2.md",
    )

    for phrase in required_phrases:
        assert phrase in documentation

    lowercase_documentation = documentation.lower()
    for unsupported_claim in ("curated demo", "live available", "408 participants"):
        assert unsupported_claim not in lowercase_documentation
