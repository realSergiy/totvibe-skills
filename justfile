sync:
    uv sync --all-groups

lint *args:
    uv run --group lint ruff check {{args}}

alias tc := typecheck

typecheck *args: lint
    uv run --group typecheck pyright {{args}}

test *args: typecheck
    uv run --group test pytest {{args}}
