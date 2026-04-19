"""Coordinate capture backends with OS-agnostic fallback behavior."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


Point = tuple[int, int]


class CoordCaptureBackend(Protocol):
    """Backend interface for collecting coordinates."""

    def collect(self, labels: list[str]) -> list[Point]:
        """Collect points in label order."""


@dataclass(slots=True)
class PynputClickBackend:
    """Collect points from mouse click events via pynput."""

    timeout_seconds: float = 20.0

    def collect(self, labels: list[str]) -> list[Point]:
        points: list[Point] = []

        try:
            from pynput.mouse import Listener  # type: ignore[import-untyped]
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("pynput を初期化できませんでした") from exc

        def on_click(
            x: int, y: int, button: object, pressed: bool
        ) -> bool | None:
            from pynput.mouse import Button  # type: ignore[import-untyped]

            if not pressed or button is not Button.right:
                return None

            idx = len(points)
            if idx < len(labels):
                print(f"座標取得 [{labels[idx]}]: {x}, {y}")
            points.append((x, y))
            if len(points) >= len(labels):
                return False
            return None

        with Listener(on_click=on_click) as listener:
            listener.join(self.timeout_seconds)
            if len(points) < len(labels):
                listener.stop()
                raise RuntimeError("クリック入力がタイムアウトしました")

        return points


@dataclass(slots=True)
class ManualInputBackend:
    """Collect points from terminal input."""

    input_func: Callable[[str], str] = input

    def collect(self, labels: list[str]) -> list[Point]:
        points: list[Point] = []
        for label in labels:
            while True:
                raw = self.input_func(
                    f"{label} の座標を x,y 形式で入力してください (例: 100,200): "
                ).strip()
                try:
                    x_str, y_str = raw.split(",", maxsplit=1)
                    x, y = int(x_str.strip()), int(y_str.strip())
                except ValueError:
                    print("入力形式が不正です。x,y 形式で再入力してください。")
                    continue

                points.append((x, y))
                break

        return points
