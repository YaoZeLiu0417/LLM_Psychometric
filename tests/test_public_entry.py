import ast
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_APP_PATH = ROOT / "public_app.py"


def test_public_entry_avoids_process_global_runpy_execution() -> None:
    tree = ast.parse(PUBLIC_APP_PATH.read_text(encoding="utf-8"))
    imported_modules = {
        node.module if isinstance(node, ast.ImportFrom) else alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "runpy" not in imported_modules


def test_public_entry_renders_project_page_on_rerun(monkeypatch) -> None:
    monkeypatch.delenv("WORKBENCH_DEPLOYMENT", raising=False)
    monkeypatch.delenv("PUBLIC_DEMO_GENERATION_LIMIT", raising=False)

    assert PUBLIC_APP_PATH.is_file(), "public_app.py must be a dedicated public entry"
    app = AppTest.from_file(str(PUBLIC_APP_PATH), default_timeout=10)
    app.session_state["v2_active_page"] = "PROJECT"

    for _ in range(2):
        app.run()
        markdown = "\n".join(element.value for element in app.markdown)
        assert not app.exception
        assert "2023 STUDY / COLLEGE STUDENT SAMPLE" in markdown
