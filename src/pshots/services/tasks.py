"""スクリーンショット取得と PDF 変換のバックグラウンド処理。"""

import shutil
import time
from importlib import import_module
from pathlib import Path
from typing import Any, TypedDict

from mss import mss
from natsort import natsorted
from PIL import Image

from pshots.config.paths import pdfs_dir, pngs_dir, trash_dir
from pshots.config.state import jobs


img2pdf: Any = import_module("img2pdf")
pyautogui: Any = import_module("pyautogui")


class CaptureCoords(TypedDict):
    bbox: tuple[int, int, int, int]
    next_x: int
    next_y: int


def capture_screenshots(
    job_id: str,
    folder: str,
    pages: int,
    delay: int,
    coords: CaptureCoords,
) -> None:
    """マウスクリックを挟みながら連続してスクリーンショットを取得する。

    引数:
        job_id: 状態追跡に使うジョブ識別子。
        folder: スクリーンショット保存先フォルダ名。
        pages: 取得するスクリーンショット枚数。
        delay: 取得開始前の待機秒数。
        coords: 'bbox'（取得範囲）と 'next_x'/'next_y'（次ページボタン座標）
            を含む辞書。
    """
    try:
        jobs[job_id]["status"] = "開始前に待機中..."
        time.sleep(delay)
        output_dir = pngs_dir / folder
        output_dir.mkdir(exist_ok=True)
        jobs[job_id]["status"] = "スクリーンショット撮影中..."

        with mss() as sct:
            for i in range(pages):
                bbox = coords["bbox"]
                monitor = {
                    "top": bbox[1],
                    "left": bbox[0],
                    "width": bbox[2] - bbox[0],
                    "height": bbox[3] - bbox[1],
                }
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                w, h = img.size
                img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
                path = output_dir / f"Page_{i + 1:03}.png"
                img.save(path, optimize=True, dpi=(300, 300))
                jobs[job_id]["progress"] = f"{i + 1}/{pages} 枚保存済み"
                pyautogui.click(coords["next_x"], coords["next_y"])
                time.sleep(1)

        jobs[job_id]["status"] = f"完了！保存先：{output_dir}"
        jobs[job_id]["done"] = True
    except Exception as e:
        jobs[job_id]["status"] = f"エラー: {e}"
        jobs[job_id]["done"] = True


def convert_to_pdf(job_id: str, target_dir: Path, save_dest: str) -> None:
    """PNG 画像群を PDF に変換し、元フォルダをアーカイブする。

    引数:
        job_id: 状態追跡に使うジョブ識別子。
        target_dir: 変換対象の PNG ファイルを含むディレクトリ。
        save_dest: 生成した PDF の保存先種別。
    """
    try:
        jobs[job_id]["status"] = "PNGファイル検索中..."
        pngs = natsorted([p for p in target_dir.glob("*.png")])
        if not pngs:
            jobs[job_id]["status"] = "エラー: PNGファイルが見つかりません。"
            jobs[job_id]["done"] = True
            return

        jobs[job_id]["status"] = "PDF変換中..."
        pdfs_dir.mkdir(exist_ok=True)
        pdf_path = pdfs_dir / f"{target_dir.name}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert([str(p) for p in pngs]))

        shutil.move(str(target_dir), trash_dir / target_dir.name)
        jobs[job_id]["status"] = (
            f"完了！PDF: {pdf_path}（元フォルダは trash へ）"
        )
        jobs[job_id]["done"] = True
    except Exception as e:
        jobs[job_id]["status"] = f"エラー: {e}"
        jobs[job_id]["done"] = True
