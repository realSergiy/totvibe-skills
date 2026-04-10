#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["polars>=1.0", "typer>=0.15", "toon-format>=0.9.0b1"]
# ///
"""Quick parquet inspection CLI."""

from __future__ import annotations

import glob as globmod
from pathlib import Path
from typing import Annotated

import polars as pl
import typer
from toon_format import encode

__version__ = "0.5.0"

app = typer.Typer()


def _version_callback(value: bool) -> None:
    if value:
        print(f"peek {__version__}")
        raise typer.Exit


def _column_types(df: pl.DataFrame) -> list[str]:
    return [str(dtype) for dtype in df.schema.dtypes()]


def _split_cols(s: str) -> list[str]:
    return [c.strip() for c in s.split(",")]


def _validate_columns(df: pl.DataFrame, columns: list[str]) -> None:
    available = set(df.schema.names())
    bad = [c for c in columns if c not in available]
    if bad:
        raise typer.BadParameter(
            f"Column(s) not found: {', '.join(bad)}. Available: {', '.join(df.schema.names())}"
        )


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
        col_list = _split_cols(cols)
        _validate_columns(df, col_list)
        df = df.select(col_list)
    total = df.shape[0]
    output: dict = {}
    preview = df if all_rows else df.head(n)
    output[stem] = preview.to_dicts()
    if types:
        output["types"] = _column_types(df)
    if not all_rows and n < total:
        output["rows"] = total
    return output


def _schema(df: pl.DataFrame, stem: str) -> dict:
    """Build TOON output dict for schema/columns mode."""
    cols = list(df.schema.names())
    types = _column_types(df)
    return {stem: dict(zip(cols, types)), "rows": df.shape[0]}


def _unique(df: pl.DataFrame, columns: str) -> dict:
    """Build TOON output dict for unique-values mode."""
    col_list = _split_cols(columns)
    _validate_columns(df, col_list)
    output: dict = {}
    for col_name in col_list:
        values = df[col_name].drop_nulls().unique().sort().to_list()
        output[col_name] = values
    return output


def _groupby(df: pl.DataFrame, columns: str) -> dict:
    """Build TOON output dict for group-by mode."""
    col_list = _split_cols(columns)
    _validate_columns(df, col_list)
    result = df.group_by(col_list).len().sort(col_list)
    return {"group": result.to_dicts()}


def _sql(frames: list[tuple[str, pl.DataFrame]], query: str) -> dict:
    """Build TOON output dict for SQL mode.

    Registers tables as t (first file), t1, t2, ..., tN.
    """
    tables: dict[str, pl.DataFrame] = {"t": frames[0][1]}
    for i, (_stem, df) in enumerate(frames, 1):
        tables[f"t{i}"] = df
    ctx = pl.SQLContext(tables)
    result = ctx.execute(query).collect()
    return {"result": result.to_dicts()}


@app.command()
def main(
    path: Annotated[list[str], typer.Argument(help="Path(s) or glob pattern(s) for parquet file(s)")],
    n: Annotated[int, typer.Option("-n", help="Number of preview rows")] = 2,
    all_rows: Annotated[bool, typer.Option("-a", help="Show all rows")] = False,
    types: Annotated[bool, typer.Option("-t", help="Include column types")] = False,
    schema: Annotated[bool, typer.Option("-c", help="Show columns and types only")] = False,
    unique: Annotated[str | None, typer.Option("-u", help="Show unique values of column(s)")] = None,
    group: Annotated[str | None, typer.Option("-g", help="Group-by column(s) with counts")] = None,
    query: Annotated[str | None, typer.Option("-q", help="SQL query (table aliased as t, t1, t2, ...)")] = None,
    cols: Annotated[str | None, typer.Option("--cols", help="Select columns for preview")] = None,
    version: Annotated[bool | None, typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version and exit")] = None,
) -> None:
    """Inspect parquet files — preview, schema, unique values, group-by, or SQL."""
    modes = [schema, unique is not None, group is not None, query is not None]
    if sum(modes) > 1:
        raise typer.BadParameter("Use only one mode at a time: -c, -u, -g, or -q")

    paths: list[Path] = []
    for p in path:
        paths.extend(_resolve_paths(p))

    # SQL mode: register all files into one query context
    if query is not None:
        frames = [(p.stem, pl.read_parquet(p)) for p in paths]
        print(encode(_sql(frames, query)))
        return

    for i, p in enumerate(paths):
        df = pl.read_parquet(p)
        stem = p.stem

        if schema:
            output = _schema(df, stem)
        elif unique is not None:
            output = _unique(df, unique)
        elif group is not None:
            output = _groupby(df, group)
        else:
            output = _preview(df, stem, n, all_rows, types, cols)

        print(encode(output))
        if i < len(paths) - 1:
            print()


if __name__ == "__main__":
    app()
