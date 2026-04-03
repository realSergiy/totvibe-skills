# totvibe-skills

A collection of CLI skills for Claude Code.

## Skills

| Skill | Description |
|-------|-------------|
| [peek](skills/peek/SKILL.md) | Inspect parquet files — preview, schema, unique values, group-by, SQL |
| [suggest](skills/suggest/SKILL.md) | Submit structured improvement suggestions for skills |

## Development

Requires [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/).

```bash
just sync        # install all deps
just l           # lint
just tc          # typecheck (lints first)
just t           # test (typechecks and lints first)
just i           # install all skills globally
just i <name>    # install a single skill globally
just u <name>    # uninstall a skill globally
```

Skills that declare a `bin` in `package.json` are automatically linked into PATH via `npm link` during install.
