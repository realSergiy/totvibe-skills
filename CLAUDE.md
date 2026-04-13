# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A collection of CLI skills for Claude Code, managed as a Python monorepo with `uv` and `just`.

## Commands

```bash
just sync        # install all deps (uv sync --all-groups)
just l           # lint (ruff)
just tc          # typecheck (pyright) — runs lint first
just t           # test (pytest) — runs typecheck first, which runs lint first
just t tests/skills/peek/test_info.py::test_default_output  # run a single test
just i peek      # install a skill globally via npx skills
just u peek      # uninstall a skill globally
```

The `just t` chain is: lint → typecheck → test. Use `just l` or `just tc` to run partial chains.

## Architecture

Each skill lives in `skills/<name>/` and must contain:

- `SKILL.md` — frontmatter with `name`, `description`, `metadata` (version, user-invocable, argument-hint), plus usage docs
- `<name>.py` — a standalone `uv run --script` CLI with inline script dependencies

Skills are self-contained Python scripts using inline `uv` script metadata (`# /// script`) so they can run without the project venv. They output **TOON** (Token-Oriented Object Notation) format for LLM-friendly structured output via the `toon-format` package.

## Testing

Tests mirror the skill structure: `tests/skills/<name>/`. Each skill's test suite uses `conftest.py` to dynamically import the skill module via `importlib` (not regular imports) and provides fixtures like `invoke` (wraps `typer.testing.CliRunner`).

`tests/test_skills_valid.py` auto-discovers all skills and validates them against the Agent Skills spec using the `skills-ref` package — every skill must pass `validate()` and have non-empty `name`/`description`.

## Versioning

Every skill change requires a version bump — patch for fixes, minor for features. Update all three locations in lockstep:

1. `skills/<name>/<name>.py` — `__version__` variable
2. `skills/<name>/package.json` — `version` field
3. `skills/<name>/SKILL.md` — `metadata.version` in frontmatter

All three must match. Use semver (`MAJOR.MINOR.PATCH`), no pre-release tags.

## Key Dependencies

- **polars** — data handling in skills (not pandas)
- **typer** — CLI framework for skills
- **toon-format** — TOON encoding/decoding for structured output
- **skills-ref** — skill validation against the Agent Skills spec
- Python **3.14+** required
