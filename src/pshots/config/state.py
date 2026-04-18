"""Global application state for job tracking."""

from __future__ import annotations


jobs: dict[str, dict[str, object]] = {}
