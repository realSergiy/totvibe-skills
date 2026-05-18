---
title: CLAUDE.md section
---

## Naming Conventions

Apply the language's idiomatic casing on top of these rules.

- Spell names out; long-and-clear over short-and-clever. Mirror domain vocabulary.
- Drop type suffixes (`array`/`str`/`int`/`bool`/`dict`).
- Replace placeholder nouns (`data`/`info`/`value`/`item`/`result`/`output`) with what it actually is.
- Replace filler verbs (`process`/`handle`/`do`/`perform`/`execute`/`manage`) with what the function actually does.
- Start every function name with a verb, picking one verb per semantic and using it consistently across the codebase:
  - `get` cheap in-memory lookup that always succeeds
  - `find` predicate search that may miss
  - `list` return a collection
  - `fetch` network I/O
  - `load` disk/cache
  - `calc` non-trivial derivation
  - `build`/`make` construct a new value
  - `parse` string → structured value
  - `serialize`/`format` structured value → string
  - `validate` check invariants, error on failure
  - `ensure` make a condition true (idempotent)
- Name variables by what they hold, not how they're stored (`original image`, not `img1`); pluralise collections, singularise items.
- Drop scope echoes — inside `User`, the field is `email`, not `user email`.
- Phrase booleans as questions (`is`/`has`/`can`/`should`); prefer positive (`has value` over `is not empty`).
- Keep properties (`@property`, TS `get`/`set`) cheap and pure — no I/O or mutation; otherwise make it a method.
- Name constants by concept, not literal (`MAX_RETRY_ATTEMPTS`, never `THREE`).
- Use noun phrases for classes and types (`order processor`, not `process order`); no `T` prefix or `Type`/`Impl` suffix.
- End error classes with `Error` (`parse address Error`); keep one word order across siblings.
