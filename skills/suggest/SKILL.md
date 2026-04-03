---
name: suggest
description: >
  Submit structured improvement suggestions for CLI skills — bugs, missing features, inefficiencies, or token waste.
  Use PROACTIVELY whenever you hit a skill gap, write a workaround, or notice verbose/redundant output.
  If a skill could be simpler, more token-efficient, or cover your use case — say so immediately, don't wait.
metadata:
  version: "0.1.0"
  user-invocable: "true"
  argument-hint: <skill-name> <markdown-text>
---

# suggest — skill improvement suggestions

Skills evolve through use. When you notice a skill falling short — wrong output, missing mode, wasteful tokens, clunky interface — submit a suggestion so it gets better.

## When to suggest

- **You wrote a workaround** — a `python -c` one-liner, extra parsing, post-processing that the skill should have handled
- **Output was wasteful** — verbose, redundant, or structured in a way that burns tokens without adding information
- **Interface could be simpler** — flags that could be merged, defaults that are wrong for the common case, inputs that require unnecessary ceremony
- **A skill errored or gave wrong results** on valid input
- **A skill you needed doesn't exist** — and the use case is common enough to justify one

Skip suggestions for user errors or things outside the skill's scope.

## Suggestion structure

Structure your suggestion around these five questions. Be concrete — vague suggestions are noise.

1. **Context** — what were you doing when you hit this?
2. **Gap** — what did you try, what happened, what should have happened? Include the command and output.
3. **Responsibility** — why should the skill handle this, not the caller? If you wrote a workaround, include it — it proves the need.
4. **Suggestion** — what should change? A new flag, different default, leaner output format?
5. **Impact** — one line: how does this fix improve the workflow?

## Usage

```
suggest <skill-name> "<markdown text following the structure above>"
```

## Example

```bash
suggest peek "## peek -c output is too verbose for multi-file scans

### Context
Scanning 12 parquet files to find which ones contain a 'user_id' column.

### Gap
\`peek data/*.parquet -c\` prints full schema for every file. I only needed column names, but got types and row counts too — ~60 lines of output when 12 would do.

### Responsibility
Schema scanning across many files is a core peek use case. The caller shouldn't need to pipe through grep to get a compact answer.

### Suggestion
Add a \`--names-only\` modifier for \`-c\` that prints just column names, one file per line. Or: make \`-c\` output more compact by default and add \`-cv\` for the verbose version.

### Impact
Cuts token usage ~5x for multi-file schema scans — the most common first step when exploring a new dataset directory."
```

## Output

```
saved: ~/Documents/skill-suggestions/peek/suggestion_20260403_141523.md
```
