"""Web routes and request handlers for screenshot/PDF tools."""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

from flask import (
    Blueprint,
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue

from pshots.config.paths import cwd
from pshots.config.state import jobs
from pshots.services.coords import COORD_JSON_PATH, load_coord_store
from pshots.services.tasks import capture_screenshots, convert_to_pdf


web_bp = Blueprint("web", __name__, template_folder="templates")


@web_bp.route("/")
def index() -> str:
    """Home page with links to screenshot and PDF conversion tools."""
    return render_template("index.html")


@web_bp.route("/screenshot", methods=["GET", "POST"])
def screenshot() -> ResponseReturnValue:
    """Screenshot capture page: display form and process submissions."""
    coord_file = COORD_JSON_PATH
    coords = None
    coord_msg = "click_coords.json が見つかりません。先に座標取得ツールを実行してください。"
    coord_store = load_coord_store(coord_file)
    coord_names = list(coord_store["profiles"].keys())
    selected_coord_name = (
        request.values.get("coord_name")
        or coord_store["default"]
        or (coord_names[0] if coord_names else "")
    )

    if coord_names:
        profile = coord_store["profiles"].get(selected_coord_name)
        if profile:
            left, top, right, bottom = profile["bbox"]
            next_x, next_y = profile["next"]
            coords = {
                "bbox": (left, top, right, bottom),
                "next_x": next_x,
                "next_y": next_y,
            }
            coord_msg = (
                f"設定名: {selected_coord_name}<br>"
                f"範囲: 左上=({left},{top}), 右下=({right},{bottom})<br>"
                f"次ページクリック位置: ({next_x},{next_y})"
            )
    elif coord_file.exists():
        coord_msg = (
            "click_coords.json の形式が不正です。座標を再登録してください。"
        )

    if request.method == "POST":
        folder = request.form.get("folder", "myshots")
        pages = int(request.form.get("pages", "5"))
        delay = int(request.form.get("delay", "5"))
        if not coords:
            return "click_coords.json が未設定です。先に座標取得してください。"

        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "status": "ジョブ開始",
            "progress": "",
            "done": False,
        }
        t = threading.Thread(
            target=capture_screenshots,
            args=(job_id, folder, pages, delay, coords),
        )
        t.start()
        return redirect(url_for(".job_status_page", job_id=job_id))

    return render_template(
        "screenshot.html",
        coord_msg=coord_msg,
        coord_names=coord_names,
        selected_coord_name=selected_coord_name,
    )


@web_bp.route("/convert", methods=["GET", "POST"])
def convert() -> ResponseReturnValue:
    """PNG to PDF conversion page: display form and process submissions."""
    dirs = [
        d
        for d in cwd.iterdir()
        if d.is_dir() and d.name not in {"shelf", "trash"}
    ]

    if request.method == "POST":
        target_folder = request.form.get("target_folder")
        save_dest = request.form.get("save_dest", "shelf")
        if target_folder is None:
            return "変換対象フォルダが指定されていません。"
        target_dir = Path(target_folder)
        if not target_dir.exists():
            return "指定された変換対象のフォルダが存在しません。"

        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "status": "ジョブ開始",
            "progress": "",
            "done": False,
        }
        t = threading.Thread(
            target=convert_to_pdf, args=(job_id, target_dir, save_dest)
        )
        t.start()
        return redirect(url_for(".job_status_page", job_id=job_id))

    folder_options = [str(d) for d in dirs]
    return render_template("convert.html", folder_options=folder_options)


@web_bp.route("/job_status/<job_id>")
def job_status_page(job_id: str) -> str:
    """Job status monitoring page with live polling."""
    return render_template("job_status.html", job_id=job_id)


@web_bp.route("/job_status/<job_id>/json")
def job_status(job_id: str) -> ResponseReturnValue:
    """JSON API endpoint for job status queries."""
    job = jobs.get(
        job_id, {"status": "不明なジョブID", "progress": "", "done": True}
    )
    return jsonify(job)


def register_routes(app: Flask) -> None:
    """Register routes by attaching the web blueprint.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(web_bp)
