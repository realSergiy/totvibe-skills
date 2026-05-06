# Install all dependencies (upgrades to latest compatible versions)
sync:
    uv sync --all-groups --upgrade

alias l := lint

# Lint (rumdl + ruff), autofix by default; pass --no-fix to report only
[arg('fix', long='no-fix', value='')]
lint fix='--fix':
    uv run --group lint rumdl check {{fix}}
    uv run --group lint ruff check {{fix}}

alias tc := typecheck

# Lint then typecheck (pyright), autofix by default; --no-fix to report only
[arg('fix', long='no-fix', value='')]
typecheck fix='--fix': (lint fix)
    uv run --group typecheck pyright

alias t := test

# Lint + typecheck + test (pytest), autofix by default; --no-fix to report only.
# Extra args go to pytest; use `--` to forward dash-flagged args (e.g. `just t -- -k expr`).
[arg('fix', long='no-fix', value='')]
test fix='--fix' *args: (typecheck fix)
    uv run --group test pytest {{args}}

alias i := install

# Install a skill globally (omit name to install all stale skills; FORCE=1 reinstalls all)
install name="":
    @uv run scripts/skillman.py install {{name}}

alias u := uninstall

# Uninstall a skill globally
uninstall name:
    @uv run scripts/skillman.py uninstall {{name}}

alias p := push

# Push current branch; opens a draft PR (-r marks ready and enables auto-merge)
push *flags:
    @uv run scripts/pusher.py {{flags}}

alias b := bump

# Bump <skill>'s version (default --minor; -p/--patch, --major). Idempotent + higher-wins.
bump *args:
    @uv run scripts/release.py bump {{args}}
