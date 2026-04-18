"""Core application module: Flask app and routing."""

from pshots.core.app import app, create_app
from pshots.core.routes import register_routes


__all__ = ["app", "create_app", "register_routes"]
