from pathlib import Path


_app_path = Path(__file__).with_name("app_v2.py")
exec(
    compile(_app_path.read_bytes(), str(_app_path), "exec"),
    {"__file__": str(_app_path), "__name__": "__main__"},
)
