# TypeScript and Python naming conventions (shared)

## Functions and methods

- **Start with a verb that names the action.** Functions are actions; their names should make the action obvious without reading the body. Prefer `calculateTotal` over `total`, `saveUser` over `userSaver`.

- **Pick the verb that matches the cost and side effects.** Use `get` only for cheap, single-item, in-memory lookups; `list` for collection scans; `find` for predicate searches that may return nothing; `fetch` for network I/O; `load` for disk or cache reads; `compute` or `calculate` for non-trivial derivations.

- **Use a consistent verb for each concept across the codebase.** If you scan-and-return-many with `list`, don't mix in `get` for the same shape of operation elsewhere; pick one verb per semantic and stick with it.

- **Boolean-returning functions read as questions.** Prefix with `is`, `has`, `can`, `should`, or `was` so call sites read like predicates, and avoid negated forms like `isNotEmpty` in favour of positive phrasing like `hasValue`.

- **Reserve property-style access (Python `@property`, TS `get`/`set` accessors) for cheap, pure reads with no side effects.** A getter must not do I/O, must not mutate observable state, and should return the same value on repeated calls unless it's a one-time cached computation.

## Variables and parameters

- **Use nouns or noun phrases that describe what the value holds, not how it's stored.** Prefer `originalImage` over `img1`, `userEmail` over `str`.

- **Use plural nouns for collections and singular for individual items.** A list of users is `users`; one element pulled from it is `user`. The plural carries cardinality, so don't append `List`, `Array`, or `Collection`.

- **Don't restate the containing context in the name.** Inside a `User` class, the field is `email`, not `userEmail`; inside an `Image` class, the field is `width`, not `imageWidth`. Context already provides the qualifier.

- **Spell out names; don't truncate by deleting letters.** Use `configuration` or `config` (an accepted abbreviation), but never `cfg`, `usr`, or `prc`. Short names are acceptable only for variables whose scope is a handful of lines, like loop counters.

- **Avoid ambiguous single letters and lookalike characters.** Skip `l`, `O`, and `I` as standalone names since they're visually indistinguishable from digits. Single letters are reserved for tight, conventional scopes like `i`, `j`, `k` in loops or `x`, `y` in coordinates.

- **Avoid placeholder or grab-bag words.** Names like `data`, `info`, `process`, `handle`, `manage`, `value`, or `object` carry no information; replace them with what the thing actually is.

## Classes, types, and interfaces

- **Name classes and types with nouns or noun phrases describing what they represent.** A class is a thing, not an action; prefer `OrderProcessor` over `ProcessOrder`.

- **Don't prefix interfaces with `I` or suffix types with `Type`.** Modern style names the interface for what it represents (`User`, `TodoItemStorage`), distinguishing it from implementations by purpose, not by a typographic marker.

- **Suffix error classes with `Error`.** Exception and error types should end in `Error` so they're recognisable at a glance; reserve other suffixes for non-error signal types.

- **Use a consistent word order across related names.** If you have `ParseAddressError`, don't also have `LookupErrorDns`; pick verb-object-error (or whichever order fits the domain) and apply it uniformly.

## Constants

- **Name constants for the concept, not the literal value.** `MAX_RETRY_ATTEMPTS` describes intent; `THREE` describes nothing. The name should still make sense if the underlying number changes.

## General principles

- **Optimise for the reader, not the writer.** Code is read far more often than written, so a slightly longer descriptive name almost always beats a clever short one. `getInitials` is better than `gi`, even though it costs more keystrokes.

- **Don't encode the type in the name.** TypeScript and Python both have type systems or annotations to carry that information; names like `userArray`, `nameStr`, or `countInt` are redundant.

- **Match the vocabulary of the domain.** Use the words your users, product, or API already use ("customer," not "client," if the domain calls them customers); a project-wide glossary of preferred terms prevents drift.

- **Prefer clarity over brevity, but cut anything that adds no meaning.** Drop filler words like `use_`, `with_`, `do_`, `perform_` unless they distinguish the function from a sibling; the verb alone usually carries the action.
