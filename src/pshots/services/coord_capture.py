"""OS 差異を吸収するフォールバック付き座標取得バックエンド。"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol


Point = tuple[int, int]


class CoordCaptureBackend(Protocol):
    """座標取得バックエンドのインターフェース。"""

    def collect(self, labels: list[str]) -> list[Point]:
        """ラベル順に座標点を収集する。"""


@dataclass(slots=True)
class PynputClickBackend:
    """pynput のマウスクリックイベントで座標点を収集する。"""

    timeout_seconds: float = 20.0

    def collect(self, labels: list[str]) -> list[Point]:
        points: list[Point] = []

        try:
            mouse_module: Any = import_module("pynput.mouse")
            listener_class: Any = mouse_module.Listener
            right_button: Any = mouse_module.Button.right
        except Exception as exc:
            raise RuntimeError("pynput を初期化できませんでした") from exc

        def on_click(
            x: int, y: int, button: object, pressed: bool
        ) -> bool | None:
            if not pressed or button is not right_button:
                return None

            idx = len(points)
            if idx < len(labels):
                print(f"座標取得 [{labels[idx]}]: {x}, {y}")
            points.append((x, y))
            if len(points) >= len(labels):
                return False
            return None

        with listener_class(on_click=on_click) as listener:
            listener.join(self.timeout_seconds)
            if len(points) < len(labels):
                listener.stop()
                raise RuntimeError("クリック入力がタイムアウトしました")

        return points


@dataclass(slots=True)
class ManualInputBackend:
    """ターミナル入力から座標点を収集する。"""

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
