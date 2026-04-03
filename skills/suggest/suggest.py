#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["typer>=0.15"]
# ///
"""Submit structured improvement suggestions for CLI skills — bugs, gaps, inefficiencies."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer

app = typer.Typer()

SUGGEST_DIR = Path.home() / "Documents" / "skill-suggestions"


def _save(skill: str, text: str) -> Path:
    """Save suggestion markdown to timestamped file. Returns the path."""
    dest = SUGGEST_DIR / skill
    dest.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = dest / f"suggestion_{ts}.md"
    path.write_text(text + "\n")
    return path


@app.command()
def main(
    skill: str = typer.Argument(help="Name of the skill to improve"),
    text: str = typer.Argument(
        help="Markdown: Context, Gap, Responsibility, Suggestion, Impact"
    ),
) -> None:
    """Submit a structured improvement suggestion for a skill — what fell short and what should change."""
    path = _save(skill, text)
    print(f"saved: {path}")


if __name__ == "__main__":
    app()
