"""Path management and directory initialization."""

from __future__ import annotations

from pathlib import Path


cwd = Path.cwd()
shelf_dir = cwd / "shelf"
trash_dir = cwd / "trash"

shelf_dir.mkdir(exist_ok=True)
trash_dir.mkdir(exist_ok=True)
