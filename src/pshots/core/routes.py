"""Web routes and request handlers for screenshot/PDF tools."""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue

from pshots.config.paths import cwd
from pshots.config.state import jobs
from pshots.services.coords import load_coord_store
from pshots.services.tasks import capture_screenshots, convert_to_pdf


def register_routes(app: Flask) -> None:
    """Register HTTP routes for the Flask application.

    Args:
        app: Flask application instance to register routes on.
    """

    @app.route("/")
    def index() -> str:
        """Home page with links to screenshot and PDF conversion tools."""
        return render_template_string(
            """
    <!doctype html>
    <html lang="ja">
    <head>
      <meta charset="utf-8">
      <title>スクショ＆PDFツール</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container py-4">
      <h1 class="mb-4">スクショ＆PDFツール</h1>
      <div class="list-group">
        <a href="{{ url_for('screenshot') }}" class="list-group-item list-group-item-action">📸 スクリーンショット保存</a>
        <a href="{{ url_for('convert') }}" class="list-group-item list-group-item-action">🧾 PNG → PDF 変換</a>
      </div>
    </body>
    </html>
    """
        )

    @app.route("/screenshot", methods=["GET", "POST"])
    def screenshot() -> ResponseReturnValue:
        """Screenshot capture page: display form and process submissions."""
        coord_file = Path("click_coords.json")
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
                return (
                    "click_coords.json が未設定です。先に座標取得してください。"
                )

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
            return redirect(url_for("job_status_page", job_id=job_id))

        return render_template_string(
            """
    <!doctype html>
    <html lang="ja">
    <head>
      <meta charset="utf-8">
      <title>スクリーンショット保存</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container py-4">
      <h1>📸 スクリーンショット保存</h1>
      <p class="text-muted">{{ coord_msg|safe }}</p>
      <form method="post">
        <div class="mb-3">
          <label class="form-label">座標設定名</label>
          <select name="coord_name" class="form-select">
            {% for name in coord_names %}
            <option value="{{ name }}" {% if name == selected_coord_name %}selected{% endif %}>{{ name }}</option>
            {% endfor %}
          </select>
          <div class="form-text">座標登録は create_box.py --name 設定名 で追加できます。</div>
        </div>
        <div class="mb-3">
          <label class="form-label">保存先フォルダ名</label>
          <input type="text" name="folder" class="form-control" value="myshots">
        </div>
        <div class="mb-3">
          <label class="form-label">キャプチャ回数</label>
          <input type="number" name="pages" class="form-control" value="5" min="1">
        </div>
        <div class="mb-3">
          <label class="form-label">開始前の待機秒数</label>
          <input type="number" name="delay" class="form-control" value="5" min="0">
        </div>
        <button type="submit" class="btn btn-primary">▶ スクショ開始</button>
      </form>
      <br>
      <a href="{{ url_for('index') }}">トップに戻る</a>
    </body>
    </html>
    """,
            coord_msg=coord_msg,
            coord_names=coord_names,
            selected_coord_name=selected_coord_name,
        )

    @app.route("/convert", methods=["GET", "POST"])
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
            return redirect(url_for("job_status_page", job_id=job_id))

        folder_options = [str(d) for d in dirs]
        return render_template_string(
            """
    <!doctype html>
    <html lang="ja">
    <head>
      <meta charset="utf-8">
      <title>PNG → PDF変換</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container py-4">
      <h1>🧾 PNG → PDF変換</h1>
      <form method="post">
        <div class="mb-3">
          <label class="form-label">変換するフォルダ</label>
          <select name="target_folder" class="form-select">
            {% for f in folder_options %}
            <option value="{{ f }}">{{ f }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="mb-3">
          <label class="form-label">保存先フォルダ（デフォルト: shelf）</label>
          <input type="text" name="save_dest" class="form-control" value="shelf">
        </div>
        <button type="submit" class="btn btn-primary">📄 PDF作成して保存</button>
      </form>
      <br>
      <a href="{{ url_for('index') }}">トップに戻る</a>
    </body>
    </html>
    """,
            folder_options=folder_options,
        )

    @app.route("/job_status/<job_id>")
    def job_status_page(job_id: str) -> str:
        """Job status monitoring page with live polling."""
        return render_template_string(
            """
    <!doctype html>
    <html lang="ja">
    <head>
      <meta charset="utf-8">
      <title>ジョブステータス</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <script>
        function fetchStatus() {
          $.getJSON("{{ url_for('job_status', job_id=job_id) }}", function(data) {
            $("#status").html(data.status + "<br>" + data.progress);
            if (!data.done) {
              setTimeout(fetchStatus, 1000);
            } else {
              $("#status").append("<br><strong>処理完了！</strong>");
            }
          });
        }
        $(document).ready(function(){
          fetchStatus();
        });
      </script>
    </head>
    <body class="container py-4">
      <h1>ジョブステータス</h1>
      <div id="status" class="alert alert-info">ステータス取得中…</div>
      <a href="{{ url_for('index') }}" class="btn btn-secondary">トップに戻る</a>
    </body>
    </html>
    """,
            job_id=job_id,
        )

    @app.route("/job_status/<job_id>/json")
    def job_status(job_id: str):
        """JSON API endpoint for job status queries."""
        job = jobs.get(
            job_id, {"status": "不明なジョブID", "progress": "", "done": True}
        )
        return jsonify(job)
