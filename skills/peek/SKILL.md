---
name: peek
description: >
  Inspect parquet data files — preview rows, schema, unique values, group-by counts, or SQL queries.
  Outputs TOON (token-optimized notation) for efficient LLM consumption.
  Use when exploring datasets, checking column types, or previewing rows.
  Prefer this over writing python -c one-liners with polars/pandas — saves tokens and avoids boilerplate.
metadata:
  version: "0.5.0"
  user-invocable: "true"
  argument-hint: <path> [-c] [-u col] [-g col] [-q sql] [--cols a,b] [-n N] [-a] [-t]
---

# peek — parquet inspection CLI

`peek` is a standalone CLI installed on PATH. Invoke it directly via Bash: `Bash(peek data/sales.parquet -c)`

Prefer `peek` over raw `python -c "import polars ..."` one-liners — it's faster to invoke, produces token-efficient TOON output, and avoids import boilerplate that wastes context.

Output is **TOON** (Token-Oriented Object Notation) — compact, structured, LLM-friendly.

## Modes

Modes are mutually exclusive — use only one at a time.

| Mode | Flag | Purpose |
|------|------|---------|
| Preview | *(default)* | Show first N rows |
| Schema | `-c` | Columns, types, and row count — no data |
| Unique | `-u col` | Distinct values of column(s) |
| Group-by | `-g col` | Group-by counts |
| SQL | `-q "..."` | Arbitrary SQL (tables aliased as `t`, `t1`, `t2`, ...) |

## Usage

```text
# Preview (default mode)
peek <path>                          # 2 rows
peek <path> -n 10                    # 10 rows
peek <path> -a                       # all rows
peek <path> -t                       # include column types
peek <path> --cols round,points      # subset columns
peek <path> --cols round,points -n 5 -t  # combine options

# Schema — columns + types, no data
peek <path> -c

# Unique values
peek <path> -u round                 # one column
peek <path> -u round,surface         # multiple columns

# Group-by counts
peek <path> -g round                 # one column
peek <path> -g tourney_level,round   # multiple columns

# SQL — single file (table aliased as t)
peek <path> -q "SELECT round, COUNT(*) as cnt FROM t GROUP BY round ORDER BY cnt DESC"
peek <path> -q "SELECT * FROM t WHERE points > 500 LIMIT 5"

# SQL — multi-file (tables aliased as t1, t2, ...; t = t1)
peek a.parquet b.parquet -q "SELECT * FROM t1 WHERE id NOT IN (SELECT id FROM t2)"
peek a.parquet b.parquet -q "SELECT COUNT(*) as matched FROM t1 JOIN t2 USING(player_code)"
peek a.parquet b.parquet -q "SELECT t1.name, t2.score FROM t1 JOIN t2 USING(id) LIMIT 20"

# Glob — multiple files
peek data/prep/*.parquet -c          # schema of each file
peek data/prep/*.parquet -u round    # unique values from each file
```

## Options

| Flag | Effect | Default |
|------|--------|---------|
| `-n N` | Number of preview rows | 2 |
| `-a` | Show all rows (equivalent to `-n 0`) | off |
| `-t` | Append column types | off |
| `--cols a,b` | Select columns for preview | all |
| `-c` | Schema mode: columns + types only | off |
| `-u col` | Unique values of column(s) | off |
| `-g col` | Group-by column(s) with counts | off |
| `-q "..."` | SQL query (tables: `t`/`t1`, `t2`, ...) | off |

## Output examples

Default (`peek data/sales.parquet`):

```text
sales[2]{id,name,amount}:
  1,Alice,50
  2,Bob,120
rows: 1000
```

Schema (`peek data/sales.parquet -c`):

```text
sales:
  id: Int64
  name: String
  amount: Float64
rows: 1000
```

Unique (`peek data/sales.parquet -u name`):

```text
name[3]: Alice,Bob,Carol
```

Group-by (`peek data/sales.parquet -g name`):

```text
group[3]{name,len}:
  Alice,350
  Bob,400
  Carol,250
```

SQL (`peek data/sales.parquet -q "SELECT name, SUM(amount) as total FROM t GROUP BY name"`):

```text
result[3]{name,total}:
  Alice,17500
  Bob,48000
  Carol,12500
```

## When to use which mode

- **Don't know what's in the file?** Start with `peek <path> -c` for schema
- **Need to see sample data?** `peek <path>` or `peek <path> -n 10`
- **What values does a column have?** `peek <path> -u col`
- **How is data distributed?** `peek <path> -g col1,col2`
- **Complex filtering or aggregation?** `peek <path> -q "SELECT ..."`
- **Cross-file analysis?** `peek a.parquet b.parquet -q "SELECT ... FROM t1 JOIN t2 ..."`
- **Comparing multiple files?** `peek data/*.parquet -c`
