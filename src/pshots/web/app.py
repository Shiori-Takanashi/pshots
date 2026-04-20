"""Flask アプリケーションのファクトリと初期化。"""

import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask


if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from pshots.web.routes import register_routes


def create_app() -> Flask:
    """Flask アプリケーションインスタンスを生成して設定する。

    戻り値:
        設定済みの Flask アプリケーションインスタンス。
    """
    app = Flask(__name__)
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":

    def open_browser() -> None:
        """http://127.0.0.1:5000/ をブラウザで開く。"""
        webbrowser.open_new("http://127.0.0.1:5000/")

    threading.Timer(1, open_browser).start()
    app.run(debug=True)
