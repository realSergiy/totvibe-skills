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


def _df_to_records(df: pl.DataFrame) -> list[dict]:
    return df.to_dicts()


def _schema_dict(df: pl.DataFrame) -> list[dict]:
    return [{"column": name, "dtype": str(dtype)} for name, dtype in df.schema.items()]


@app.command()
def info(
    path: Annotated[Path, typer.Argument(help="Path to a parquet file")],
    n: Annotated[int, typer.Option("-n", help="Number of preview rows")] = 2,
) -> None:
    """Show schema, shape, and a preview of a parquet file."""
    df = _read(path)
    output = {
        "rows": df.shape[0],
        "schema": _schema_dict(df),
        "preview": _df_to_records(df.head(n)),
    }
    print(encode(output))


@app.command()
def head(
    path: Annotated[Path, typer.Argument(help="Path to a parquet file")],
    n: Annotated[int, typer.Option("-n", help="Number of rows to show")] = 2,
) -> None:
    """Print the first N rows of a parquet file."""
    df = _read(path).head(n)
    output = {
        "rows": _df_to_records(df),
    }
    print(encode(output))


@app.command(name="repr")
def repr_cmd(
    path: Annotated[Path, typer.Argument(help="Path to a parquet file")],
    n: Annotated[int, typer.Option("-n", help="Number of rows in repr")] = 2,
) -> None:
    """Print a copy-pasteable Polars constructor for a parquet file."""
    df = _read(path).head(n)
    output = {
        "constructor": df.to_init_repr(),
    }
    print(encode(output))


if __name__ == "__main__":
    app()
