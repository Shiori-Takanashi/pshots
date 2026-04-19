"""Coordinate profile storage and loading from JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from pshots.config.paths import json_dir
from pshots.config.project_root import find_project_root


class CoordProfile(TypedDict):
    """Single coordinate profile: capture area and button position."""

    bbox: list[int]
    next: list[int]


class CoordStore(TypedDict):
    """Complete coordinate storage with default and profiles."""

    default: str
    profiles: dict[str, CoordProfile]


PROJECT_ROOT = find_project_root(Path(__file__))
COORD_JSON_PATH = json_dir / "click_coords.json"
LEGACY_COORD_TXT_PATH = PROJECT_ROOT / "click_coords.txt"


def _load_legacy_txt(path: Path) -> CoordStore:
    """Load coordinate data from legacy TXT format.

    Args:
        path: Path to click_coords.txt file.

    Returns:
        CoordStore dictionary with migrated data.
    """
    if not path.exists():
        return {"default": "", "profiles": {}}

    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if len(lines) < 3:
        return {"default": "", "profiles": {}}

    try:
        left, top = map(int, lines[0].split(","))
        right, bottom = map(int, lines[1].split(","))
        next_x, next_y = map(int, lines[2].split(","))
    except ValueError:
        return {"default": "", "profiles": {}}

    return {
        "default": "default",
        "profiles": {
            "default": {
                "bbox": [left, top, right, bottom],
                "next": [next_x, next_y],
            }
        },
    }


def load_coord_store(path: Path = COORD_JSON_PATH) -> CoordStore:
    """Load coordinate store from JSON, with fallback to legacy TXT.

    Args:
        path: Path to click_coords.json file.

    Returns:
        CoordStore with default and named coordinate profiles.
    """
    if not path.exists():
        legacy = _load_legacy_txt(LEGACY_COORD_TXT_PATH)
        if legacy["profiles"]:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(legacy, f, ensure_ascii=False, indent=2)
            return legacy
        return {"default": "", "profiles": {}}

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    default = data.get("default", "")
    profiles = data.get("profiles", {})
    if not isinstance(default, str) or not isinstance(profiles, dict):
        return {"default": "", "profiles": {}}

    normalized_profiles: dict[str, CoordProfile] = {}
    for name, profile in profiles.items():
        if not isinstance(name, str) or not isinstance(profile, dict):
            continue
        bbox = profile.get("bbox")
        next_pos = profile.get("next")
        if (
            isinstance(bbox, list)
            and isinstance(next_pos, list)
            and len(bbox) == 4
            and len(next_pos) == 2
            and all(isinstance(v, int) for v in bbox)
            and all(isinstance(v, int) for v in next_pos)
        ):
            normalized_profiles[name] = {"bbox": bbox, "next": next_pos}

    if default not in normalized_profiles:
        default = next(iter(normalized_profiles), "")

    return {"default": default, "profiles": normalized_profiles}


def save_coord_profile(
    name: str,
    left_top: tuple[int, int],
    right_bottom: tuple[int, int],
    next_pos: tuple[int, int],
    path: Path = COORD_JSON_PATH,
) -> None:
    """Save a named coordinate profile to JSON storage.

    Args:
        name: Profile name (identifier).
        left_top: (x, y) coordinates of capture area top-left.
        right_bottom: (x, y) coordinates of capture area bottom-right.
        next_pos: (x, y) coordinates of page-advance button.
        path: Path to click_coords.json file.
    """
    store = load_coord_store(path)
    store["profiles"][name] = {
        "bbox": [left_top[0], left_top[1], right_bottom[0], right_bottom[1]],
        "next": [next_pos[0], next_pos[1]],
    }
    store["default"] = name

    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
