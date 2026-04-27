# Install all dependencies
sync:
    uv sync --all-groups

alias l := lint

# Lint (rumdl + ruff), autofix by default; pass --no-fix to report only
lint *args:
    @uv run scripts/dev.py lint {{args}}

alias tc := typecheck

# Lint then typecheck (pyright), autofix by default; --no-fix to report only
typecheck *args:
    @uv run scripts/dev.py typecheck {{args}}

alias t := test

# Lint + typecheck + test (pytest), autofix by default; --no-fix to report only
test *args:
    @uv run scripts/dev.py test {{args}}

alias i := install

# Install a skill globally (omit name to install all stale skills; FORCE=1 reinstalls all)
install name="":
    @uv run scripts/skillman.py install {{name}}

alias u := uninstall

# Uninstall a skill globally
uninstall name:
    @uv run scripts/skillman.py uninstall {{name}}

alias p := push

# Push current branch; opens a draft PR or finalizes (-r merges after checks)
push *flags:
    @uv run scripts/pusher.py {{flags}}

alias b := bump

# Bump <skill>'s version (default --minor; -p/--patch, --major). Idempotent + higher-wins.
bump *args:
    @uv run scripts/release.py bump {{args}}
