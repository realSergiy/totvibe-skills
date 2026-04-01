# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
just sync        # install all deps
just l           # lint (ruff)
just tc          # typecheck (ruff → pyright)
just t           # test (typecheck → pytest)
just t tests/skills/peek/test_info.py        # single test file
just t -k test_exits_successfully            # by keyword
just i peek      # install skill globally (npx skills add + npm link)
```

The test recipe chains: lint → typecheck → pytest. Use `uv run --group test pytest <args>` to skip the chain.

## Architecture

Skills live in `skills/<name>/` with three files:

- **SKILL.md** — YAML frontmatter (name, description, user-invocable) + usage docs for agent discovery
- **package.json** — declares `bin` mapping command name → script; used by `npm link` to make the CLI globally available after install
- **script.py** — standalone PEP 723 executable with `#!/usr/bin/env -S uv run --script` shebang and inline dependencies; no package structure needed

Tests mirror the skill path: `tests/skills/<name>/`. Fixtures in `conftest.py` provide a `runner` (Typer CliRunner), `invoke(command, *args)` helper, and `decode()` for TOON output.

## Tooling

- Python >=3.14, managed by **uv** (dependency groups: test, lint, typecheck)
- **ruff** for linting, **pyright** for type checking — both use defaults, no custom config
- Skills use TOON format (token-optimized object notation) for LLM-friendly output
