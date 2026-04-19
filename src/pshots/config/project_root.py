"""プロジェクトルート探索ユーティリティ。"""

from pathlib import Path


MARKER_FILES = ("pyproject.toml", ".git")


def find_project_root(start: Path | None = None) -> Path:
    """マーカーファイルを基準に上位ディレクトリからルートを探索する。

    引数:
        start: 上方向探索の開始パス。省略時は現在の作業ディレクトリを
            使用する。

    戻り値:
        検出したプロジェクトルートのパス。マーカーファイルが見つからない
        場合は現在の作業ディレクトリを返す。
    """
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if any((candidate / marker).exists() for marker in MARKER_FILES):
            return candidate

    return Path.cwd().resolve()
