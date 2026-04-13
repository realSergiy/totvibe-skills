# h2md skill + cli

## Purpose

- h2md exists to **minimize** agent token spend on web content ingestion.
- The CLI performs all deterministic work — fetching, extraction, HTML-to-markdown conversion, normalization, linting, and artifact detection — so the agent only spends tokens on surgical edits to fix remaining artifacts.
- Information must be carried over without loss; the resulting markdown should be clean and readable but does not need to match the original page layout.
