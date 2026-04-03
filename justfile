# Install all dependencies
sync:
    uv sync --all-groups

alias l := lint

# Run linters (rumdl + ruff), pass --fix to auto-fix
lint *args:
    rumdl check {{args}}
    uv run --group lint ruff check {{args}}

alias tc := typecheck

# Run typecheck (pyright), lints first
typecheck *args: lint
    uv run --group typecheck pyright {{args}}

alias t := test

# Run tests (pytest), typechecks and lints first
test *args: typecheck
    uv run --group test pytest {{args}}

alias i := install

# Install a skill globally (omit name to install all)
install name="":
    #!/usr/bin/env bash
    if [ -z "{{name}}" ]; then
        for skill in skills/*/SKILL.md; do
            s="$(basename "$(dirname "$skill")")"
            just install "$s"
        done
    else
        npx skills add . -g --skill {{name}} -y
        chmod +x "$HOME/.agents/skills/{{name}}/{{name}}.py"
        test -f "$HOME/.agents/skills/{{name}}/package.json" && (cd "$HOME/.agents/skills/{{name}}" && npm link) || true
    fi

alias u := uninstall

# Uninstall a skill globally
uninstall name:
    test -f "$HOME/.agents/skills/{{name}}/package.json" && (cd "$HOME/.agents/skills/{{name}}" && npm unlink) || true
    npx skills remove {{name}} -g -y
