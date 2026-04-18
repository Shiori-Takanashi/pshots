"""Screenshot and PDF conversion web application.

Packages:
  - core: Flask app factory and web routing
  - services: Background tasks (screenshot capture, PDF conversion) and coordinate storage
  - config: Global configuration (paths, job state)
  - cli: Command-line tools (coordinate capture)
"""

__all__ = ["main"]


def main() -> None:
    """Entry point for pshots command-line tool."""
    from pshots.core.app import app

    app.run(debug=True)
