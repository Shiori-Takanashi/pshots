"""Screenshot and PDF conversion web application.

Packages:
  - core: Flask app factory and web routing
  - services: Background tasks (screenshot capture, PDF conversion) and coordinate storage
  - config: Global configuration (paths, job state)
  - cli: Command-line tools (coordinate capture)
"""

from __future__ import annotations

import argparse


__all__ = ["main"]


def _run_web_mode(args: argparse.Namespace) -> None:
    from pshots.core.app import create_app

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="pshots 実行コマンド")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--web",
        action="store_true",
        help="Webモードを起動",
    )
    mode_group.add_argument(
        "--cli",
        action="store_true",
        help="CLIモードを起動（対話式）",
    )
    parser.add_argument("--host", default="127.0.0.1", help="バインド先ホスト")
    parser.add_argument("--port", type=int, default=5000, help="待受ポート")
    parser.add_argument("--debug", action="store_true", help="デバッグモード")

    return parser


def main() -> None:
    """Entry point for pshots command-line tool."""
    from pshots.cli.interactive import run_cli_interactive

    parser = _build_parser()
    args = parser.parse_args()
    if args.cli:
        run_cli_interactive()
        return
    _run_web_mode(args)
