---
name: peek
description: >
  Inspect parquet data files — preview rows, column types, row count.
  Outputs TOON (token-optimized notation) for efficient LLM consumption.
  Use when exploring datasets, checking column types, or previewing rows.
  ALWAYS use this instead of writing python -c one-liners with polars/pandas.
user-invocable: true
argument-hint: <path> [-n N] [-a] [-t]
---

# peek — parquet inspection CLI

NEVER write raw `python -c "import polars ..."` one-liners to inspect parquet files. Use `peek` instead.

Output is **TOON** (Token-Oriented Object Notation) — compact, structured, LLM-friendly.

## Usage

```
peek <path>              Preview first 2 rows
peek <path> -n 10        Preview first 10 rows
peek <path> -a           Show all rows (no truncation)
peek <path> -t           Include column types after the table
peek <path> -n 5 -t      Combine options
```

## Options

| Flag | Effect | Default |
|------|--------|---------|
| `-n N` | Number of preview rows | 2 |
| `-a` | Show all rows (equivalent to `-n 0`) | off |
| `-t` | Append column types | off |

## Output

The table key is the **file stem** (filename without `.parquet`).

Default (`peek data/sales.parquet`):
```
sales[2]{id,name,amount}:
  1,Alice,50
  2,Bob,120
rows: 1000
```

`rows` is shown automatically when the preview is truncated. It is hidden when all rows are displayed (`-a`, `-n 0`, or `-n` >= total rows).

With `-t`:
```
sales[2]{id,name,amount}:
  1,Alice,50
  2,Bob,120
types[3]: Int64,String,Float64
rows: 1000
```

## When to use

- Exploring an unfamiliar parquet file — start with `peek <path>`
- Need column names and types — use `peek <path> -t`
- Need full data for analysis — use `peek <path> -a`
- Need more context rows — use `peek <path> -n 20`
