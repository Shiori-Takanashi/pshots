"""座標プロファイルの JSON 保存と読み込み。"""

import json
from pathlib import Path
from typing import TypedDict

from pshots.config.paths import json_dir
from pshots.config.root import find_root


class CoordProfile(TypedDict):
    """単一の座標プロファイル: 取得範囲とボタン位置。"""

    bbox: list[int]
    next: list[int]


class CoordStore(TypedDict):
    """既定値と複数プロファイルを持つ座標ストア。"""

    default: str
    profiles: dict[str, CoordProfile]


root = find_root(Path(__file__))
COORD_JSON_PATH = json_dir / "click_coords.json"
LEGACY_COORD_TXT_PATH = root / "click_coords.txt"


def _load_legacy_txt(path: Path) -> CoordStore:
    """旧式 TXT 形式の座標データを読み込む。

    引数:
        path: click_coords.txt ファイルのパス。

    戻り値:
        移行済みデータを含む CoordStore 辞書。
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
    """JSON から座標ストアを読み込む。存在しない場合は旧式 TXT を使う。

    引数:
        path: click_coords.json ファイルのパス。

    戻り値:
        既定値と名前付き座標プロファイルを含む CoordStore。
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
    """名前付き座標プロファイルを JSON ストレージへ保存する。

    引数:
        name: プロファイル名（識別子）。
        left_top: 取得範囲左上の (x, y) 座標。
        right_bottom: 取得範囲右下の (x, y) 座標。
        next_pos: ページ送りボタンの (x, y) 座標。
        path: click_coords.json ファイルのパス。
    """
    store = load_coord_store(path)
    store["profiles"][name] = {
        "bbox": [left_top[0], left_top[1], right_bottom[0], right_bottom[1]],
        "next": [next_pos[0], next_pos[1]],
    }
    store["default"] = name

    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
