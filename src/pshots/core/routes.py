"""Web routes and request handlers for screenshot/PDF tools."""

from __future__ import annotations

import threading
import uuid

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

from pshots.config.paths import pngs_dir
from pshots.config.state import jobs
from pshots.services.coord_capture import PynputClickBackend
from pshots.services.coords import (
    COORD_JSON_PATH,
    load_coord_store,
    save_coord_profile,
)
from pshots.services.tasks import capture_screenshots, convert_to_pdf


web_bp = Blueprint("web", __name__, template_folder="templates")
WEB_CLICK_TIMEOUT_SECONDS = 60.0


def _normalize_folder_name(raw: str | None, default: str = "") -> str:
    """Return a safe single-segment folder name.

    Reject both '/' and '\\' so behavior does not differ by OS path rules.
    """
    value = (raw or default).strip() or default
    if not value:
        raise ValueError("フォルダ名を入力してください。")
    if "/" in value or "\\" in value:
        raise ValueError(
            "フォルダ名に区切り文字（/ または \\）は使用できません。"
        )
    if value in {".", ".."}:
        raise ValueError("フォルダ名が不正です。")
    return value


@web_bp.route("/")
def index() -> str:
    """Home page with links to screenshot and PDF conversion tools."""
    return render_template("index.html")


@web_bp.route("/coords", methods=["GET", "POST"])
def coords_register() -> ResponseReturnValue:
    """Coordinate registration page for web mode."""
    message = ""
    message_kind = "info"
    coord_store = load_coord_store(COORD_JSON_PATH)
    coord_names = list(coord_store["profiles"].keys())
    selected_name = request.args.get("name") or coord_store["default"]
    selected_profile = coord_store["profiles"].get(selected_name)

    if request.method == "GET" and request.args.get("saved") == "1":
        message = "座標を登録しました。内容を確認してください。"
        message_kind = "success"

    if request.method == "POST":
        name = (request.form.get("name") or "default").strip() or "default"
        selected_name = name
        capture_mode = (request.form.get("capture_mode") or "manual").strip()

        labels = ["左上", "右下", "次ページボタン"]
        points: list[tuple[int, int]]

        if not message:
            try:
                if capture_mode == "click":
                    points = PynputClickBackend(
                        timeout_seconds=WEB_CLICK_TIMEOUT_SECONDS
                    ).collect(labels)
                elif capture_mode == "manual":
                    points = [
                        (
                            int(request.form["left_top_x"]),
                            int(request.form["left_top_y"]),
                        ),
                        (
                            int(request.form["right_bottom_x"]),
                            int(request.form["right_bottom_y"]),
                        ),
                        (
                            int(request.form["next_x"]),
                            int(request.form["next_y"]),
                        ),
                    ]
                else:
                    return (
                        "capture_mode は click か manual を指定してください。"
                    )
            except (KeyError, ValueError):
                message = "manual ではすべての座標を整数で入力してください。"
                message_kind = "danger"
            except RuntimeError as exc:
                if capture_mode == "click":
                    message = "座標登録に失敗しました。60秒以内に3点を右クリックしてください。"
                else:
                    message = str(exc)
                message_kind = "danger"
            else:
                save_coord_profile(
                    name=name,
                    left_top=points[0],
                    right_bottom=points[1],
                    next_pos=points[2],
                )
                return redirect(
                    url_for(".coords_register", saved="1", name=name)
                )

    if request.method == "POST":
        coord_store = load_coord_store(COORD_JSON_PATH)
        coord_names = list(coord_store["profiles"].keys())
        selected_name = selected_name or coord_store["default"]
        selected_profile = coord_store["profiles"].get(selected_name)

    return render_template(
        "coords.html",
        message=message,
        message_kind=message_kind,
        coord_names=coord_names,
        coord_default=coord_store["default"],
        selected_name=selected_name,
        selected_profile=selected_profile,
    )


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
        try:
            folder = _normalize_folder_name(
                request.form.get("folder"), default="myshots"
            )
        except ValueError as exc:
            return str(exc)
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
    dirs = (
        [d for d in pngs_dir.iterdir() if d.is_dir()]
        if pngs_dir.exists()
        else []
    )

    if request.method == "POST":
        target_folder = request.form.get("target_folder")
        save_dest = request.form.get("save_dest", "shelf")
        if target_folder is None:
            return "変換対象フォルダが指定されていません。"
        try:
            folder_name = _normalize_folder_name(target_folder)
        except ValueError as exc:
            return str(exc)

        target_dir = pngs_dir / folder_name
        if not target_dir.exists() or not target_dir.is_dir():
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

    folder_options = [d.name for d in dirs]
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
