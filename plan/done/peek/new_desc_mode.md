# Describe mode

Add -d describe mode

This fills a real gap in the exploration workflow. Currently peek answers:

- "What columns exist?" → -c
- "What does sample data look like?" → default preview
- "What's the shape/distribution of the data?" → nothing. You need multiple commands or a custom query.

A describe mode would output one compact line per column:

```text
data{5 cols, 1000 rows}:
id(Int64): min=1 max=1000 mean=500.5 null=0
name(Str): unique=42 null=3 top=Alice(350)
amount(Float64): min=0.5 max=9999.0 mean=450.2 std=312.1 null=0
date(Date): min=2024-01-01 max=2024-12-31 null=0
category(Str): unique=5 null=0 top=electronics(423)
```

This is extremely token-efficient (one line per column) and gives the LLM everything needed to understand data quality (nulls), distribution (min/max/mean), and cardinality (unique counts) in a single invocation. Polars describe() outputs a wide table that's verbose in TOON;
this is a purpose-built summary.

It's the most common "next question" after schema inspection, it's cheap to implement using Polars' built-in stats, and it saves 2-3 round trips that currently require separate -u, -g, and -q calls.

Another option:

```bash
peek data.parquet -d
  stats{col,type,nulls,unique,min,max,mean}:
    round,String,0,11,,,
    points,Int32,0,45,8,2000,312.5
  rows: 94
```

Imperative to consider:

- which output format will be the best
- does it need to be a flag like `peek data.parquet -d` or should it be the default mode `peek data.parquet`
