# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A collection of skills for Claude Code, managed as a Python monorepo with `uv` and `just`. Skills come in two kinds — `cli` (ship an executable) and `prompt` (SKILL.md-driven) — declared via `metadata.kind` in the skill's frontmatter (see Architecture).

## Commands

```bash
just sync        # install all deps (uv sync --all-groups)
just l           # lint (rumdl + ruff), autofixes by default
just tc          # typecheck (pyright) — runs lint first
just t           # test (pytest) — runs typecheck first, which runs lint first
just t --no-fix    # same chain, no autofix (mirrors what CI does)
just t tests/skills/peek/test_info.py::test_default_output  # run a single test
just i peek      # install a single skill globally (default source: github main)
just i           # install every skill whose source version differs from the installed copy
FORCE=1 just i   # force-reinstall every skill, ignoring version match
just u peek      # uninstall a skill globally
just p           # push branch + open draft PR (pass -r to mark ready, wait for checks, squash-merge)
just b mermaid   # bump a skill's version (default minor; -p for patch, --major; idempotent + higher-wins)
```

The `just t` chain is: lint → typecheck → test, **with autofix on lint by default** (since `just …` is local-only). Pass `--no-fix` to mirror CI's no-autofix behavior. Chain logic lives in [scripts/dev.py](scripts/dev.py); CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) calls the underlying tools directly without autofix.

Install/uninstall logic lives in [scripts/skillman.py](scripts/skillman.py) — a single PEP 723 + typer CLI invoked by the one-line just recipes. Subcommands: `install [NAME]`, `uninstall NAME`, `list-stale`. Defaults to fetching skill content from `github:realSergiy/totvibe-skills` so installs reflect what's been merged on `main`. Pass `--source .` (or set `SKILLMAN_SOURCE=.`) to install from the local working tree when developing.

### Per-skill environment variables

A skill that needs runtime env vars declares them in `skills/<name>/env.toml`:

```toml
[env]
SKILL_FOO_DIR = "{repo_root}/some/path"
```

`{repo_root}` and `{skill_dir}` are interpolated at install time. `skillman install` writes the rendered values to `~/.config/environment.d/skill_<name>.conf` and exports them in `~/.bashrc`. `skillman uninstall` removes both. Prefix variable names with `SKILL_` to avoid collisions with system env.

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

Versions follow semver (`MAJOR.MINOR.PATCH`, no pre-release tags) and are bumped manually as part of each PR. `tests/test_skills_valid.py::test_skill_changes_require_version_bump` enforces the rule: if a skill directory diffs against `origin/main`, its `SKILL.md` version must too — CI fails otherwise.

For `kind: cli` skills, the bump updates three files in lockstep — `<name>.py` (`__version__`), `package.json` (`version`), and `SKILL.md` (`metadata.version`). For `kind: prompt` skills, only `SKILL.md` carries a version.

Use `just b <skill>` (alias of `just bump`) to bump. Default is `--minor`; pass `-p` for patch or `--major` for major. The bump is **idempotent** (re-running with the same kind is a no-op) and **higher-wins** (a lower kind never downgrades a higher one; a higher kind resets the lower-order parts). The base for both decisions is the version on `origin/main`, so each PR ends up with at most one bump per skill regardless of how many times you push. PR scope changing mid-flight (chore → feat → feat!) is handled by re-running with the new kind.

## CI / Branch protection

Repo settings and `main` branch protection live declaratively in [.github/settings.yml](.github/settings.yml). Policy:

- Direct pushes to `main` blocked; PRs only (admins included — `enforce_admins: true`)
- Squash merges only (merge / rebase disabled), linear history required, branch deleted on merge
- Required status checks: `lint (rumdl)`, `lint (ruff)`, `typecheck (pyright)`, `test (pytest)`, `claude code review`
- Code owner review required for paths in [.github/CODEOWNERS](.github/CODEOWNERS) (currently `/.github/`, owned by `@realSergiy`)

Workflows:

- [ci.yml](.github/workflows/ci.yml) — lint / typecheck / test on every PR and push to main.
- [claude-review.yml](.github/workflows/claude-review.yml) — runs the official `code-review` plugin on non-draft PRs (required status check).
- [claude-pr-summary.yml](.github/workflows/claude-pr-summary.yml) — on every push to a draft PR, refreshes the title and body. Two independent opt-in markers in the body (`<!-- remove this line to stop claude updating the pr title -->` and `<!-- remove this line to stop claude updating the pr summary -->`) gate each part; remove a marker to opt out. Title is rewritten in Conventional Commits format on every push (re-evaluating type as the PR evolves). `pusher.py -r` strips all HTML comments before merge so markers don't leak into the squash commit.
- [claude.yml](.github/workflows/claude.yml) — runs Claude when `@claude` is mentioned in a PR/issue comment, review, or issue body.

The three GitHub Apps that power these workflows (Settings, Claude Code, Copilot) are listed in the README. Install them once; everything else is wired up in this repo.

## Key Dependencies

- **polars** — data handling in skills (not pandas)
- **typer** — CLI framework for skills
- **toon-format** — TOON encoding/decoding for structured output
- **skills-ref** — skill validation against the Agent Skills spec
- Python **3.14+** required
