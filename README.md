# totvibe-skills

A collection of CLI skills for Claude Code.

## Skills

| Skill | Description |
|-------|-------------|
| [peek](skills/peek/SKILL.md) | Inspect parquet files — schema, preview, Polars constructor |

## Development

Requires [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/).

```bash
just sync        # install all deps
just l           # lint
just tc          # typecheck (lint → typecheck)
just t           # test (typeckeck -> test)
just i <name>    # install a skill globally
```

Skills that declare a `bin` in `package.json` are automatically linked into PATH via `npm link` during install.
