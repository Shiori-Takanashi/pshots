"""Web アプリケーションモジュール: Flask アプリとルーティング。"""

from pshots.web.app import app, create_app
from pshots.web.routes import register_routes


__all__ = ["app", "create_app", "register_routes"]
