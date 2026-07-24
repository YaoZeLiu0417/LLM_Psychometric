from pathlib import Path
from runpy import run_path


run_path(str(Path(__file__).with_name("app_v2.py")))
