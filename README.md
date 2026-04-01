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
just test        # lint → typecheck → test
just lint        # ruff
just tc          # pyright
```
