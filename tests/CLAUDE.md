# Tests

**Rule: test through the public interface only.**

CLI skills and scripts → invoke via `typer.testing.CliRunner` (or the `invoke` fixture from the skill's `conftest.py`) and assert exit code, output, and on-disk effects. Don't import helper functions and call them directly.

Prompt skills → assert against the artifact the skill produces, not internal scratch.

`justfile` recipes are dev-only orchestration; don't test them. Test the script they call.

**Why:** helper-level unit tests pass while the CLI itself breaks (typer subcommand collapse, arg-parser regressions, wrong exit codes — none of which are visible from inside a function) and fail spuriously during refactors that didn't change user-visible behavior. Tests anchored to the CLI surface stay aligned with what users actually run.
