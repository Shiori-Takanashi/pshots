"""Background task execution for screenshot capture and PDF conversion."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import TypedDict

import img2pdf  # type: ignore[import-untyped]
import pyautogui  # type: ignore[import-untyped]
from mss import mss
from natsort import natsorted
from PIL import Image

from pshots.config.paths import cwd, trash_dir
from pshots.config.state import jobs


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
    """Capture sequential screenshots with mouse clicks between captures.

    Args:
        job_id: Unique job identifier for status tracking.
        folder: Output folder name for screenshots.
        pages: Number of screenshots to capture.
        delay: Initial delay before starting captures.
        coords: Dictionary with 'bbox' (capture rectangle) and 'next_x'/'next_y'
                (button coordinates to advance to next page).
    """
    try:
        jobs[job_id]["status"] = "開始前に待機中..."
        time.sleep(delay)
        output_dir = cwd / folder
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
                path = output_dir / f"Page_{i + 1:03}.png"
                img.save(path)
                jobs[job_id]["progress"] = f"{i + 1}/{pages} 枚保存済み"
                pyautogui.click(coords["next_x"], coords["next_y"])
                time.sleep(1)

        jobs[job_id]["status"] = f"完了！保存先：{output_dir}"
        jobs[job_id]["done"] = True
    except Exception as e:
        jobs[job_id]["status"] = f"エラー: {e}"
        jobs[job_id]["done"] = True


def convert_to_pdf(job_id: str, target_dir: Path, save_dest: str) -> None:
    """Convert PNG images to PDF and archive source folder.

    Args:
        job_id: Unique job identifier for status tracking.
        target_dir: Directory containing PNG files to convert.
        save_dest: Output folder name for generated PDF.
    """
    try:
        jobs[job_id]["status"] = "PNGファイル検索中..."
        pngs = natsorted([p for p in target_dir.glob("*.png")])
        if not pngs:
            jobs[job_id]["status"] = "エラー: PNGファイルが見つかりません。"
            jobs[job_id]["done"] = True
            return

        jobs[job_id]["status"] = "PDF変換中..."
        output_folder = cwd / save_dest
        output_folder.mkdir(exist_ok=True)
        pdf_path = output_folder / f"{target_dir.name}.pdf"
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
