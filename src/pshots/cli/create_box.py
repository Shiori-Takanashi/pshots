"""Interactive tool to capture screen coordinates and save to JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from pshots.services.coord_capture import ManualInputBackend, PynputClickBackend
from pshots.services.coords import save_coord_profile


def main() -> None:
    """Run interactive coordinate capture tool.

    Click three points in order:
    1. Top-left of capture area
    2. Bottom-right of capture area
    3. Page-advance button location
    """
    parser = argparse.ArgumentParser(
        description="クリック座標をJSONに保存します"
    )
    parser.add_argument("--name", default="default", help="座標設定名")
    parser.add_argument(
        "--mode",
        choices=["auto", "click", "manual"],
        default="auto",
        help="座標取得方式: auto(推奨), click, manual",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="click モードの待機秒数",
    )
    args = parser.parse_args()

    labels = ["左上", "右下", "次ページボタン"]

    points: list[tuple[int, int]]
    if args.mode == "manual":
        points = ManualInputBackend().collect(labels)
    else:
        print("クリックで 3 点を順番に入力してください（左/右どちらでも可）。")
        try:
            points = PynputClickBackend(timeout_seconds=args.timeout).collect(
                labels
            )
        except RuntimeError as exc:
            if args.mode == "click":
                raise SystemExit(str(exc)) from exc
            print(f"click 方式で取得できませんでした: {exc}")
            print("manual 方式に自動フォールバックします。")
            points = ManualInputBackend().collect(labels)

    save_coord_profile(
        name=args.name,
        left_top=points[0],
        right_bottom=points[1],
        next_pos=points[2],
    )
    print(f"click_coords.json に '{args.name}' として保存しました")


if __name__ == "__main__":
    main()
