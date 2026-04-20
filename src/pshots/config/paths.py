"""パス管理とディレクトリ初期化。"""

from pathlib import Path

from pshots.config.root import find_root


# 既存モジュールとの後方互換性のため `cwd` を維持する。
root = find_root(Path(__file__))
cwd = root
shelf_dir = cwd / "shelf"
trash_dir = cwd / "trash"
json_dir = cwd / "json"
pngs_dir = cwd / "pngs"
pdfs_dir = cwd / "pdfs"

shelf_dir.mkdir(exist_ok=True)
trash_dir.mkdir(exist_ok=True)
json_dir.mkdir(exist_ok=True)
pngs_dir.mkdir(exist_ok=True)
pdfs_dir.mkdir(exist_ok=True)
