# totvibe-skills

A collection of skills for Claude Code.

## Skills

| Skill | Kind | Description |
|-------|------|-------------|
| [peek](skills/peek/SKILL.md) | cli | Inspect parquet files — preview, schema, unique values, group-by, SQL |
| [h2md](skills/h2md/SKILL.md) | cli | Convert web articles to clean, faithful markdown |
| [suggest](skills/suggest/SKILL.md) | cli | Submit structured improvement suggestions for skills |
| [gen-commit-message](skills/gen-commit-message/SKILL.md) | prompt | Generate a Conventional Commits message for the current project |
| [mermaid](skills/mermaid/SKILL.md) | prompt | Pick the right Mermaid diagram type and render it correctly |
| [plan-storm](skills/plan-storm/SKILL.md) | prompt | Brainstorm a `plan.md` through option-rich rounds before any code |

Each skill declares `metadata.kind` in its SKILL.md: `cli` skills ship an executable (installed via `just i <name>`); `prompt` skills are SKILL.md-driven with no binary. Omitting `metadata.kind` defaults to `prompt`.

## Development

Requires [uv](https://docs.astral.sh/uv/), [just](https://just.systems/), and the [GitHub CLI](https://cli.github.com/) (`gh`).

```bash
just sync        # install all deps
just l           # lint (autofixes; pass --no-fix to skip)
just tc          # typecheck (lints first)
just t           # test (typechecks and lints first)
just i           # install every skill globally (from github main; force with FORCE=1)
just i <name>    # install a single skill
just u <name>    # uninstall a skill
just p           # push branch + open draft PR (-r marks ready, waits, squash-merges)
```

Skills declaring a `bin` in `package.json` are linked into `PATH` via `npm link` on install.

## GitHub apps

Three apps must be installed on the repo for the workflows to work end-to-end:

- [Settings](https://github.com/apps/settings) — applies [.github/settings.yml](.github/settings.yml) (branch protection, merge mode, code owners) on every push.
- [Claude Code](https://github.com/apps/claude) — powers PR review, draft-PR summary, and `@claude` mentions.
- GitHub Copilot — second AI reviewer, enabled in repo settings.
