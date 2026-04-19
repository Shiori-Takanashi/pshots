"""Path management and directory initialization."""

from __future__ import annotations

from pathlib import Path

from pshots.config.project_root import find_project_root


# Keep `cwd` for backward compatibility in existing modules.
project_root = find_project_root(Path(__file__))
cwd = project_root
shelf_dir = cwd / "shelf"
trash_dir = cwd / "trash"

shelf_dir.mkdir(exist_ok=True)
trash_dir.mkdir(exist_ok=True)
