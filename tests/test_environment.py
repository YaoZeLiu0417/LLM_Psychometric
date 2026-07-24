from pathlib import Path

from psychometric_v2 import __version__


def test_package_has_v2_version() -> None:
    assert __version__ == "2.0.0-demo"


def test_streamlit_cloud_has_root_requirements_entrypoint() -> None:
    requirements = Path("requirements.txt")

    assert requirements.is_file()
    assert requirements.read_text(encoding="utf-8").strip() == "-r requirements-v2.txt"


def test_secret_and_generated_paths_are_ignored() -> None:
    ignored = Path(".gitignore").read_text(encoding="utf-8")

    for pattern in (
        ".env",
        ".streamlit/secrets.toml",
        "workspace_data/",
        "*.log",
    ):
        assert pattern in ignored
