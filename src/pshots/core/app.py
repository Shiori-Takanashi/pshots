"""Flask application factory and initialization."""

from __future__ import annotations

import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask


if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from pshots.core.routes import register_routes


def create_app() -> Flask:
    """Create and configure Flask application instance.

    Returns:
        Flask: Configured application instance.
    """
    app = Flask(__name__)
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":

    def open_browser() -> None:
        """Open browser to http://127.0.0.1:5000/."""
        webbrowser.open_new("http://127.0.0.1:5000/")

    threading.Timer(1, open_browser).start()
    app.run(debug=True)
