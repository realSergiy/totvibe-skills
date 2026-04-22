# totvibe-skills

A collection of skills for Claude Code.

## Skills

| Skill | Kind | Description |
|-------|------|-------------|
| [peek](skills/peek/SKILL.md) | cli | Inspect parquet files — preview, schema, unique values, group-by, SQL |
| [h2md](skills/h2md/SKILL.md) | cli | Convert web articles to clean, faithful markdown |
| [suggest](skills/suggest/SKILL.md) | cli | Submit structured improvement suggestions for skills |
| [gen-commit-message](skills/gen-commit-message/SKILL.md) | prompt | Generate a Conventional Commits message for the current project |

Each skill declares `metadata.kind` in its SKILL.md: `cli` skills ship an executable (installable via `just i <name>`); `prompt` skills are SKILL.md-driven with no binary. Omitting `metadata.kind` defaults to `prompt`.

## Development

Requires [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/).

```bash
just sync        # install all deps
just l           # lint
just tc          # typecheck (lints first)
just t           # test (typechecks and lints first)
just i           # install all cli skills globally
just i <name>    # install a single cli skill globally
just u <name>    # uninstall a cli skill globally
```

Skills that declare a `bin` in `package.json` are automatically linked into PATH via `npm link` during install.
