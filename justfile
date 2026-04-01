sync:
    uv sync --all-groups

alias l := lint

lint *args:
    uv run --group lint ruff check {{args}}

alias tc := typecheck

typecheck *args: lint
    uv run --group typecheck pyright {{args}}

alias t := test

test *args: typecheck
    uv run --group test pytest {{args}}

alias i := install

install name:
    npx skills add . -g --skill {{name}} -y
    test -f "$HOME/.agents/skills/{{name}}/package.json" && (cd "$HOME/.agents/skills/{{name}}" && npm link) || true
