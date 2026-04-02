#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["polars>=1.0", "typer>=0.15", "toon-format @ git+https://github.com/toon-format/toon-python.git"]
# ///
"""Quick parquet inspection CLI."""

from __future__ import annotations

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


@app.command()
def main(
    path: Annotated[Path, typer.Argument(help="Path to a parquet file")],
    n: Annotated[int, typer.Option("-n", help="Number of preview rows")] = 2,
    all_rows: Annotated[bool, typer.Option("-a", help="Show all rows")] = False,
    types: Annotated[bool, typer.Option("-t", help="Include column types")] = False,
) -> None:
    """Preview a parquet file, optionally with column types."""
    df = _read(path)
    total = df.shape[0]
    show_all = all_rows or n == 0
    output: dict = {}
    preview = df if show_all else df.head(n)
    output[path.stem] = preview.to_dicts()
    if types:
        output["types"] = _column_types(df)
    if not show_all and n < total:
        output["rows"] = total
    print(encode(output))


if __name__ == "__main__":
    app()
