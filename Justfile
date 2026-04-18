# ==========================================
# Global Settings
# ==========================================

set dotenv-load := true

TARGETS := "src tests"
HOOK_TYPES := "pre-commit pre-push"

# ==========================================
# Default Task
# ==========================================

default:
    @just --list

# ==========================================
# Git Hook
# ==========================================


hooks:
    @for hook in {{HOOK_TYPES}}; do \
        echo "Installing hook: $hook ..."; \
        uv run pre-commit install --hook-type $hook; \
    done

# ==========================================
# Modification
# ==========================================

modify:
    uv run ruff check --fix {{TARGETS}}
    uv run ruff format {{TARGETS}}

# ==========================================
# Verification
# ==========================================

verify: rufy type test

rufy:
    uv run ruff check {{TARGETS}}
    uv run ruff format --check {{TARGETS}}

type:
    uv run mypy {{TARGETS}}

test:
    uv run pytest

# ==========================================
# Run Package
# ==========================================

run *args:
    uv run python -m your_package {{args}}
