'''
Central filesystem layout for runtime state.

All durable / temporary bot files live under DATA_DIR (default: <project>/data,
overridable with the DATA_DIR env var). In Docker that is typically /app/data
when WORKDIR is /app, matching a single volume mount.
'''
from __future__ import annotations

import os
import shutil
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SRC_DIR.parent


def get_data_dir() -> Path:
    env = os.environ.get("DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (_PROJECT_ROOT / "data").resolve()


def ensure_data_dir() -> Path:
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "session_cookies").mkdir(exist_ok=True)
    return data_dir


def data_path(*parts: str | os.PathLike[str]) -> str:
    """Join path segments under DATA_DIR and return an absolute string path."""
    path = ensure_data_dir().joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def seed_bundled_assets() -> None:
    """Copy read-only defaults from src/ into data/ the first time they are needed."""
    ensure_data_dir()
    bundled = {
        "conversation starters.txt": _SRC_DIR / "conversation starters.txt",
    }
    for name, source in bundled.items():
        dest = Path(data_path(name))
        if source.is_file() and not dest.exists():
            shutil.copy2(source, dest)

    # Migrate leftover runtime files from older layouts into data/
    migrate_candidates = [
        _SRC_DIR / "Focus_Mode_Info.db",
        _PROJECT_ROOT / "Focus_Mode_Info.db",
        _SRC_DIR / ".study_bot.lock",
        _PROJECT_ROOT / ".study_bot.lock",
    ]
    for source in migrate_candidates:
        dest = Path(data_path(source.name))
        if source.is_file() and not dest.exists():
            shutil.move(str(source), dest)

    old_cookies = _PROJECT_ROOT / "session_cookies"
    new_cookies = Path(data_path("session_cookies"))
    if old_cookies.is_dir():
        for item in old_cookies.iterdir():
            target = new_cookies / item.name
            if item.is_file() and not target.exists():
                shutil.copy2(item, target)


def use_data_cwd() -> Path:
    """Point process cwd at DATA_DIR so plain relative opens also land there."""
    data_dir = ensure_data_dir()
    seed_bundled_assets()
    os.chdir(data_dir)
    return data_dir
