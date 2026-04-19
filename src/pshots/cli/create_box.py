"""画面座標を対話的に取得して JSON へ保存するツール。"""

from pshots.services.coord_capture import ManualInputBackend, PynputClickBackend
from pshots.services.coords import save_coord_profile


def run_create_box(
    name: str,
    capture_mode: str = "click",
    timeout: float = 20.0,
) -> None:
    """対話形式で座標を取得し、プロファイルとして保存する。

    引数:
        name: プロファイル名。
        capture_mode: 座標取得方式。`click` または `manual`。
        timeout: `click` モードでのタイムアウト秒数。
    """
    labels = ["左上", "右下", "次ページボタン"]

    points: list[tuple[int, int]]
    if capture_mode == "manual":
        points = ManualInputBackend().collect(labels)
    elif capture_mode == "click":
        print("クリックで 3 点を順番に入力してください（左/右どちらでも可）。")
        try:
            points = PynputClickBackend(timeout_seconds=timeout).collect(labels)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        raise ValueError("capture_mode は click か manual を指定してください")

    save_coord_profile(
        name=name,
        left_top=points[0],
        right_bottom=points[1],
        next_pos=points[2],
    )
    print(f"click_coords.json に '{name}' として保存しました")
