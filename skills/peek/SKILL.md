---
name: peek
description: >
  Inspect parquet data files — schema, preview rows, Polars constructor repr.
  Outputs in TOON format (token-optimized) for efficient LLM consumption.
  Use when exploring datasets, checking column types, previewing rows, or generating
  sample data. ALWAYS use this instead of writing python -c one-liners with polars.
user-invocable: true
argument-hint: Provide the command (info, head, repr) and the path to a parquet file
---

# peek — parquet inspection CLI

NEVER write raw `python -c "import polars ..."` one-liners. Use peek instead.

All output is in **TOON format** (Token-Oriented Object Notation) for compact, LLM-friendly consumption.

## Commands

```
peek info <path> [-n N]   Row count, schema + preview (default 2 rows)
peek head <path> [-n N]   First N rows in TOON tabular format (default 2)
peek repr <path> [-n N]   Copy-pasteable Polars constructor (default 2 rows)
```

## Output structure

**`info`** returns:
```
rows: 1000
schema[5]{column,dtype}:
  id,Int64
  name,String
  ...
preview[2]{id,name,...}:
  1,Alice,...
  2,Bob,...
```

**`head`** returns:
```
rows[N]{col1,col2,...}:
  val1,val2,...
```

**`repr`** returns:
```
constructor: pl.DataFrame(...)
```

## Examples

```bash
peek info data/prep/sackmann_matches.parquet
peek info data/prep/sackmann_matches.parquet -n 10
peek head data/prep/sackmann_players.parquet -n 50
peek repr data/prep/sackmann_players.parquet -n 3
```
