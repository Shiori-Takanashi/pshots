"""Web ルートで使う共通操作をまとめたモジュール。"""

import threading
import uuid
from pathlib import Path

from werkzeug.datastructures import ImmutableMultiDict

from pshots.config.state import jobs
from pshots.services.coord_capture import PynputClickBackend
from pshots.services.coords import CoordProfile
from pshots.services.tasks import (
    CaptureCoords,
    capture_screenshots,
    convert_to_pdf,
)


def normalize_folder_name(raw: str | None, default: str = "") -> str:
    """安全な単一セグメントのフォルダ名を返す。

    引数:
        raw: 入力されたフォルダ名文字列。
        default: 空入力時に使う既定値。

    戻り値:
        検証済みのフォルダ名。

    例外:
        ValueError: 空文字、区切り文字、相対移動名が含まれる場合。
    """
    value = (raw or default).strip() or default
    if not value:
        raise ValueError("フォルダ名を入力してください。")
    if "/" in value or "\\" in value:
        raise ValueError(
            "フォルダ名に区切り文字（/ または \\）は使用できません。"
        )
    if value in {".", ".."}:
        raise ValueError("フォルダ名が不正です。")
    return value


def collect_click_or_manual_points(
    capture_mode: str,
    form: ImmutableMultiDict[str, str],
    timeout_seconds: float,
) -> list[tuple[int, int]]:
    """座標入力方式に応じて 3 点の座標を取得する。

    引数:
        capture_mode: `click` または `manual`。
        form: POST フォームデータ。
        timeout_seconds: click モード時の待機秒数。

    戻り値:
        左上、右下、次ページボタンの順で並ぶ座標リスト。

    例外:
        KeyError: manual モードで必須入力が不足している場合。
        ValueError: manual モードで整数変換できない値が含まれる場合。
        RuntimeError: click モードがタイムアウトした場合。
    """
    labels = ["左上", "右下", "次ページボタン"]

    if capture_mode == "click":
        return PynputClickBackend(timeout_seconds=timeout_seconds).collect(
            labels
        )

    return [
        (
            int(form["left_top_x"]),
            int(form["left_top_y"]),
        ),
        (
            int(form["right_bottom_x"]),
            int(form["right_bottom_y"]),
        ),
        (
            int(form["next_x"]),
            int(form["next_y"]),
        ),
    ]


def profile_to_capture_coords(
    profile: CoordProfile | None,
) -> CaptureCoords | None:
    """座標プロファイル辞書をスクリーンショット処理用の形式へ変換する。

    引数:
        profile: 座標プロファイル（`bbox` と `next` を含む辞書）。

    戻り値:
        変換済み座標辞書。入力が無効な場合は `None`。
    """
    if profile is None:
        return None

    bbox = profile.get("bbox")
    next_pos = profile.get("next")
    if (
        not isinstance(bbox, list)
        or not isinstance(next_pos, list)
        or len(bbox) != 4
        or len(next_pos) != 2
    ):
        return None

    left, top, right, bottom = bbox
    next_x, next_y = next_pos
    return {
        "bbox": (left, top, right, bottom),
        "next_x": next_x,
        "next_y": next_y,
    }


def build_coord_message(
    selected_coord_name: str,
    profile: CoordProfile | None,
) -> str:
    """表示用の座標メッセージを生成する。

    引数:
        selected_coord_name: 選択中の座標設定名。
        profile: 座標プロファイル。

    戻り値:
        テンプレート表示用の HTML 文字列。
    """
    if profile is None:
        return "click_coords.json が見つかりません。先に座標取得ツールを実行してください。"

    left, top, right, bottom = profile["bbox"]
    next_x, next_y = profile["next"]
    return (
        f"設定名: {selected_coord_name}<br>"
        f"範囲: 左上=({left},{top}), 右下=({right},{bottom})<br>"
        f"次ページクリック位置: ({next_x},{next_y})"
    )


def start_capture_job(
    folder: str,
    pages: int,
    delay: int,
    coords: CaptureCoords,
) -> str:
    """スクリーンショット取得ジョブを開始してジョブ ID を返す。

    引数:
        folder: 保存先フォルダ名。
        pages: 取得枚数。
        delay: 開始前待機秒数。
        coords: 取得範囲とクリック座標。

    戻り値:
        開始したジョブの ID。
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "ジョブ開始",
        "progress": "",
        "done": False,
    }
    thread = threading.Thread(
        target=capture_screenshots,
        args=(job_id, folder, pages, delay, coords),
    )
    thread.start()
    return job_id


def start_convert_job(target_dir: Path, save_dest: str) -> str:
    """PDF 変換ジョブを開始してジョブ ID を返す。

    引数:
        target_dir: 変換対象 PNG ディレクトリ。
        save_dest: PDF の保存先種別。

    戻り値:
        開始したジョブの ID。
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "ジョブ開始",
        "progress": "",
        "done": False,
    }
    thread = threading.Thread(
        target=convert_to_pdf,
        args=(job_id, target_dir, save_dest),
    )
    thread.start()
    return job_id
