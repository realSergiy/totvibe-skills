"""justfile_helper — local wrappers around lint/typecheck/test that autofix by default.

CI calls the underlying tools directly (without autofix). These wrappers exist
so local runs (`just l` / `just tc` / `just t`) auto-fix lint issues for you.
Pass `--no-fix` to skip autofix and report only.

Note: `--no-fix` only — no `-k` short form, since pytest already uses `-k` for
its keyword expression filter and the wrappers forward extra args verbatim.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

REPO_ROOT = Path(__file__).resolve().parents[1]

app = typer.Typer(add_completion=False, no_args_is_help=True)
_PASSTHROUGH = {"allow_extra_args": True, "ignore_unknown_options": True}


def _run(*args: str) -> None:
    subprocess.run(args, cwd=REPO_ROOT, check=True)


def _lint(no_fix: bool, extra: list[str]) -> None:
    fix = [] if no_fix else ["--fix"]
    _run("rumdl", "check", *fix, *extra)
    _run("uv", "run", "--group", "lint", "ruff", "check", *fix, *extra)


def _typecheck(no_fix: bool, extra: list[str]) -> None:
    _lint(no_fix, [])
    _run("uv", "run", "--group", "typecheck", "pyright", *extra)


def _test(no_fix: bool, extra: list[str]) -> None:
    _typecheck(no_fix, [])
    _run("uv", "run", "--group", "test", "pytest", *extra)


@app.command(context_settings=_PASSTHROUGH)
def lint(
    ctx: typer.Context,
    no_fix: bool = typer.Option(False, "--no-fix", help="Don't autofix; report only."),
) -> None:
    """Run rumdl + ruff. Autofixes by default."""
    _lint(no_fix, ctx.args)


@app.command(context_settings=_PASSTHROUGH)
def typecheck(
    ctx: typer.Context,
    no_fix: bool = typer.Option(False, "--no-fix", help="Don't autofix lint; report only."),
) -> None:
    """Lint then run pyright."""
    _typecheck(no_fix, ctx.args)


@app.command(context_settings=_PASSTHROUGH)
def test(
    ctx: typer.Context,
    no_fix: bool = typer.Option(False, "--no-fix", help="Don't autofix lint; report only."),
) -> None:
    """Lint, typecheck, then run pytest. Extra args go to pytest."""
    _test(no_fix, ctx.args)


if __name__ == "__main__":
    app()
