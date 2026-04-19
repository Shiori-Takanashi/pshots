"""Interactive CLI flow for coordinate profile creation."""

from __future__ import annotations

from pshots.cli.create_box import run_create_box


def _prompt_text(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def _prompt_capture_mode(default: str = "click") -> str:
    while True:
        raw = input(f"座標取得方式 click/manual [{default}]: ").strip().lower()
        value = raw or default
        if value in {"click", "manual"}:
            return value
        print("click か manual を入力してください。")


def _prompt_timeout(default: float = 20.0) -> float:
    while True:
        raw = input(f"click待機秒数 [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = float(raw)
        except ValueError:
            print("数値を入力してください。")
            continue
        if value < 0:
            print("0以上の値を入力してください。")
            continue
        return value


def run_cli_interactive() -> None:
    """Run create-box flow via interactive prompts."""
    print("CLIモードを開始します。")
    print("実行コマンド: create-box")

    name = _prompt_text("座標設定名", "default")
    capture_mode = _prompt_capture_mode("click")
    timeout = _prompt_timeout(20.0) if capture_mode == "click" else 20.0

    run_create_box(
        name=name,
        capture_mode=capture_mode,
        timeout=timeout,
    )
