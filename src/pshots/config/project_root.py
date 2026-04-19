"""Project root discovery utilities."""

from __future__ import annotations

from pathlib import Path


MARKER_FILES = ("pyproject.toml", ".git")


def find_project_root(start: Path | None = None) -> Path:
    """Find project root by walking upward and checking marker files.

    Args:
        start: Start path for upward search. If omitted, current working
            directory is used.

    Returns:
        Detected project root path. Falls back to current working directory
        when no marker file is found.
    """
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if any((candidate / marker).exists() for marker in MARKER_FILES):
            return candidate

    return Path.cwd().resolve()
