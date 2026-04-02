#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["polars>=1.0", "typer>=0.15", "toon-format @ git+https://github.com/toon-format/toon-python.git"]
# ///
"""Quick parquet inspection CLI."""

from __future__ import annotations

import glob as globmod
from pathlib import Path
from typing import Annotated

import polars as pl
import typer
from toon_format import encode

app = typer.Typer()


def _read(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path)


def _column_types(df: pl.DataFrame) -> list[str]:
    return [str(dtype) for dtype in df.schema.dtypes()]


def _resolve_paths(pattern: str) -> list[Path]:
    """Resolve a path or glob pattern to a list of parquet files."""
    matches = sorted(globmod.glob(pattern))
    if not matches:
        raise typer.BadParameter(f"No files match: {pattern}")
    paths = [Path(m) for m in matches]
    for p in paths:
        if not p.is_file():
            raise typer.BadParameter(f"Not a file: {p}")
    return paths


def _preview(df: pl.DataFrame, stem: str, n: int, all_rows: bool, types: bool, cols: str | None) -> dict:
    """Build TOON output dict for preview mode."""
    if cols:
        col_list = [c.strip() for c in cols.split(",")]
        df = df.select(col_list)
    total = df.shape[0]
    show_all = all_rows or n == 0
    output: dict = {}
    preview = df if show_all else df.head(n)
    output[stem] = preview.to_dicts()
    if types:
        output["types"] = _column_types(df)
    if not show_all and n < total:
        output["rows"] = total
    return output


def _schema(df: pl.DataFrame, stem: str) -> dict:
    """Build TOON output dict for schema/columns mode."""
    cols = list(df.schema.names())
    types = _column_types(df)
    return {stem: dict(zip(cols, types)), "rows": df.shape[0]}


def _unique(df: pl.DataFrame, columns: str) -> dict:
    """Build TOON output dict for unique-values mode."""
    output: dict = {}
    for col_name in (c.strip() for c in columns.split(",")):
        values = df[col_name].drop_nulls().unique().sort().to_list()
        output[col_name] = values
    return output


def _groupby(df: pl.DataFrame, columns: str) -> dict:
    """Build TOON output dict for group-by mode."""
    col_list = [c.strip() for c in columns.split(",")]
    result = df.group_by(col_list).len().sort(col_list)
    return {"group": result.to_dicts()}


def _sql(df: pl.DataFrame, query: str) -> dict:
    """Build TOON output dict for SQL mode."""
    ctx = pl.SQLContext({"t": df})
    result = ctx.execute(query).collect()
    return {"result": result.to_dicts()}


@app.command()
def main(
    path: Annotated[str, typer.Argument(help="Path or glob pattern for parquet file(s)")],
    n: Annotated[int, typer.Option("-n", help="Number of preview rows")] = 2,
    all_rows: Annotated[bool, typer.Option("-a", help="Show all rows")] = False,
    types: Annotated[bool, typer.Option("-t", help="Include column types")] = False,
    schema: Annotated[bool, typer.Option("-c", help="Show columns and types only")] = False,
    unique: Annotated[str | None, typer.Option("-u", help="Show unique values of column(s)")] = None,
    group: Annotated[str | None, typer.Option("-g", help="Group-by column(s) with counts")] = None,
    query: Annotated[str | None, typer.Option("-q", help="SQL query (table aliased as t)")] = None,
    cols: Annotated[str | None, typer.Option("--cols", help="Select columns for preview")] = None,
) -> None:
    """Inspect parquet files — preview, schema, unique values, group-by, or SQL."""
    modes = [schema, unique is not None, group is not None, query is not None]
    if sum(modes) > 1:
        raise typer.BadParameter("Use only one mode at a time: -c, -u, -g, or -q")

    paths = _resolve_paths(path)

    for i, p in enumerate(paths):
        df = _read(p)
        stem = p.stem

        if schema:
            output = _schema(df, stem)
        elif unique is not None:
            output = _unique(df, unique)
        elif group is not None:
            output = _groupby(df, group)
        elif query is not None:
            output = _sql(df, query)
        else:
            output = _preview(df, stem, n, all_rows, types, cols)

        print(encode(output))
        if i < len(paths) - 1:
            print()


if __name__ == "__main__":
    app()
