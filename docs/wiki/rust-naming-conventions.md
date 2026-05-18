# Rust naming conventions

## Casing

- **Types, traits, enums:** `UpperCamelCase` (`HashMap`, `Iterator`). Acronyms count as one word: `Uuid`, `Stdin`, not `UUID` or `StdIn`.
- **Values (functions, methods, variables, modules, crates):** `snake_case`. Acronyms are lowercased: `is_xid_start`, not `is_XID_start`.
- **Constants and statics:** `SCREAMING_SNAKE_CASE` (`MAX_SIZE`, `PI`).
- **Macros:** `snake_case!` for function-like (`println!`), `UpperCamelCase` for derive macros (`#[derive(Debug)]`).
- **Lifetimes and type parameters:** short lowercase for lifetimes (`'a`, `'src`); single uppercase letter or short name for type params (`T`, `K`, `V`, `Err`, `Item`).
- **Single-letter words:** avoid except as the final word; prefer `btree_map` over `b_tree_map`, but `PI_2` is fine.

## Getters and setters

- **No `get_` prefix on getters.** Use the bare field name: `fn first(&self) -> &First`, not `get_first()`. Mutable variants append `_mut`: `first_mut()`.
- **`get` is reserved** for cases where there is one obvious thing to get, like `Cell::get`, or for indexed lookups returning `Option` (`HashMap::get`).
- **Setters use `set_`:** `set_name(&mut self, name: String)`. Setters are increasingly rare in idiomatic Rust — prefer builders or direct field access.
- **Unchecked variants:** indexed getters with bounds checking pair with `unsafe fn get_unchecked` for the elided-check version.

## Conversion methods

- **`as_*`** — cheap, borrowed-to-borrowed view, no allocation (`str::as_bytes`). Should be near-free.
- **`to_*`** — expensive or allocating conversion, often borrowed-to-owned (`str::to_lowercase`, `Path::to_str` which validates UTF-8).
- **`into_*`** — consuming conversion, takes `self` by value and transfers ownership (`String::into_bytes`).
- **`from_*`** — constructor-style conversion *into* the type (`String::from_utf8`, `Vec::from_iter`).
- **`into_inner`** — unwrap a single-value wrapper to retrieve what it wraps (`BufReader::into_inner`).

## Iterators

- **Method triad:** `iter()` returns `&T` items, `iter_mut()` returns `&mut T` items, `into_iter()` consumes and returns `T` items.
- **Iterator type name matches the producing method:** `iter()` returns `Iter`, `into_iter()` returns `IntoIter`, `drain()` returns `Drain`. Qualify with the module (`vec::IntoIter`) to keep names compact.
- **Free-function iterators take the activity name:** `percent_encode` returns a `PercentEncode` iterator; no `iter_` prefix needed when there's only one way to iterate.

## Predicates and questions

- **Boolean methods start with `is_`, `has_`, or `can_`:** `is_empty()`, `has_root()`, `can_read()`. Reserve these prefixes for booleans only.
- **Avoid negative predicates.** Prefer `is_empty()` and negate at the call site over `is_not_empty()`.

## Constructors and builders

- **Primary constructor is `new`:** `Vec::new()`, `String::new()`. Takes no arguments or only essential ones.
- **Alternative constructors use `with_*` for configuration** (`Vec::with_capacity`) and `from_*` for conversions from another type (`String::from`).
- **Builders use fluent `snake_case` methods that take `self` and return `Self`:** `ClientBuilder::timeout(self, d).retries(self, n).build()`. The final method is conventionally `build()`.

## Traits

- **Prefer verbs, then nouns, then adjectives:** `Read`, `Write`, `Iterator`, `Display`, `Clone`. Avoid `-able` suffixes (`Copy`, not `Copyable`).
- **If a trait has one dominant method, the trait and method often share a name:** `trait Clone { fn clone(&self) -> Self; }`, `trait Hash { fn hash(...); }`.
- **Conversion traits use the `From`/`Into` pair:** implement `From` and get `Into` for free via the blanket impl. Same pattern for `TryFrom`/`TryInto`.

## Errors

- **Error types end in `Error`:** `ParseIntError`, `io::Error`.
- **Word order is verb-object-error:** `ParseAddrError`, not `AddrParseError`. Mirror this for any new error type.
- **Don't stutter with module names:** inside module `io`, name the error `Error` so it reads as `io::Error`, not `io::IoError`.

## Modules, crates, and features

- **Items inside a module aren't prefixed with the module name:** `io::Error`, not `io::IoError`. Callers can rename on import if there's a clash.
- **Crate names don't use `-rs` or `-rust`** as a prefix or suffix. Every crate is Rust.
- **Cargo features are free of filler words:** name the feature `serde`, not `use-serde` or `with-serde`. Features are additive, so negative names like `no-std` are wrong — invert it to `std`.

## Cross-cutting principles

- **Don't repeat context.** On a `Crate`, name the field `version`, not `crate_version`; on a `CrateRegistry`, name the method `installed()`, not `list_installed_crates()`.
- **Pluralize collections:** `crates: Vec<Crate>`, not `crate_list`. The plural carries the cardinality.
- **Match cost to vocabulary.** Cheap views use `as_*` and bare nouns; expensive operations use `to_*`, `compute_*`, or explicit verbs so the cost is visible at the call site.
- **Word order is consistent within a crate.** Pick one order (e.g. verb-object) and apply it everywhere; mixing `ParseAddrError` and `AddrParseError` in the same crate is a bug.
