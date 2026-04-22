# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A collection of skills for Claude Code, managed as a Python monorepo with `uv` and `just`. Skills come in two kinds — `cli` (ship an executable) and `prompt` (SKILL.md-driven) — declared via `metadata.kind` in the skill's frontmatter (see Architecture).

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

Each skill lives in `skills/<name>/` and must contain a `SKILL.md` whose frontmatter declares `name`, `description`, and `metadata` (including `kind`, `version`, and optionally `user-invocable` / `argument-hint`).

### Skill kinds

`metadata.kind` selects the shape of the skill. Two values are valid; omitting the field defaults to `prompt`:

- **`cli`** — skill ships an executable. Requires `<name>.py` (a standalone `uv run --script` CLI with inline script dependencies) and a `package.json` with a matching `version` and a `bin` entry. Installable globally via `just i <name>`. Emits **TOON** (Token-Oriented Object Notation) for LLM-friendly structured output via the `toon-format` package.
- **`prompt`** (default) — SKILL.md-driven only. No executable. Claude performs the work directly using its built-in tools, guided by the SKILL.md body and any files under `references/` / `assets/`.

The `kind ⇔ layout` invariant is enforced by `tests/test_skills_valid.py::test_skill_kind_matches_layout` — a `cli` skill without `<name>.py`, or a `prompt` skill that ships one, fails validation.

## Testing

Tests mirror the skill structure: `tests/skills/<name>/`. Each skill's test suite uses `conftest.py` to dynamically import the skill module via `importlib` (not regular imports) and provides fixtures like `invoke` (wraps `typer.testing.CliRunner`).

`tests/test_skills_valid.py` auto-discovers all skills and validates them against the Agent Skills spec using the `skills-ref` package — every skill must pass `validate()` and have non-empty `name`/`description`.

## Versioning

Every skill change requires a version bump — patch for fixes, minor for features. Use semver (`MAJOR.MINOR.PATCH`), no pre-release tags.

For `kind: cli` skills, update all three locations in lockstep:

1. `skills/<name>/<name>.py` — `__version__` variable
2. `skills/<name>/package.json` — `version` field
3. `skills/<name>/SKILL.md` — `metadata.version` in frontmatter

For `kind: prompt` skills, only `SKILL.md` carries a version (there is no `.py` or `package.json`).

## Key Dependencies

- **polars** — data handling in skills (not pandas)
- **typer** — CLI framework for skills
- **toon-format** — TOON encoding/decoding for structured output
- **skills-ref** — skill validation against the Agent Skills spec
- Python **3.14+** required
