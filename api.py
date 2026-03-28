"""Dev entry: ASGI app lives in src.main; reload watches only `src/` so `.venv` is ignored."""

from pathlib import Path

import uvicorn

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if not _SRC.is_dir():
    raise RuntimeError(f"Expected {_SRC} to exist (keep api.py at project root).")


def _reload_exclude_dirs() -> list[str]:
    """Absolute paths; limits spurious reloads if the reloader ever watches the repo root."""
    out: list[str] = []
    for name in (".venv", ".chroma", ".git"):
        p = _ROOT / name
        if p.is_dir():
            out.append(str(p.resolve()))
    return out


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(_SRC.resolve())],
        reload_excludes=_reload_exclude_dirs(),
    )
