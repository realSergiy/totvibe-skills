# New skill proposal: `a2m` (article-to-markdown)

## Context

Just finished a task where the user asked me to convert a blog post (<https://deno.com/blog/v2.7>) to markdown and save it to a local file, with the explicit requirement "full information, not a summary." No existing skill handles this cleanly, so I reached for `WebFetch` + manual markdown authoring.

## Gap

My actual workflow for that task:

1. `WebFetch(url, prompt="extract everything, all code, all headings...")`. The fetch tool runs the fetched HTML through a *small* model with a prompt I write. That model is free to paraphrase, drop sections, reorder, or miss code examples. I have no way to verify completeness without re-fetching.
2. I then hand-authored the markdown file, effectively re-expressing what the small model returned.
3. I had no access to the raw HTML, so I couldn't cross-check any ambiguous section without burning another WebFetch round trip.
4. I had to make on-the-fly decisions about markdown structure (heading levels, fenced code blocks, link formatting) that are purely mechanical and belong in a deterministic step.
5. No lint/format pass — the output was whatever I typed by hand. On a longer article I would almost certainly leave `MD*` violations behind (line length, duplicate headings, ordered list numbering, trailing whitespace).

The correctness risk is real: if the small-model extraction drops a code example or renames a flag, I have no deterministic check against the source, and I ship the drop to the user.

## Responsibility

Everything up to "final prose polish" is mechanical and should not live in the agent:

- URL fetch (with JS rendering when needed) — a tool, not a prompt.
- HTML → markdown conversion — `pandoc`/`trafilatura`/`readability-lxml`/`monolith` do this faithfully; a language model should not.
- Metadata extraction (title, author, publish date, canonical URL, OG tags, JSON-LD) — deterministic HTML parsing.
- Markdown linting/auto-fix — `rumdl check --fix` (the user already uses rumdl).
- Producing a *workspace* the agent can re-read cheaply instead of re-fetching.

The agent's job is the last mile: fix anything the converters mangled (tables, nested code, callouts), tidy headings for LLM/human readability, verify against the stored raw HTML — not to be the conversion engine.

## Suggestion

### CLI: `a2m <url> [--out DIR] [--engine pandoc|trafilatura|readability] [--render] [--force]`

Default behavior: create a workspace directory and populate it deterministically. Nothing is deleted on re-run unless `--force` is passed; each stage is skipped if its output already exists (cheap resume).

### Workspace layout (everything the agent might need, one place)

```text
<out>/<slug>/
  source.url              # the original URL, one line
  raw.html                # exact bytes from the server (or rendered DOM if --render)
  raw.headers.json        # response headers, final URL after redirects, fetch timestamp
  readable.html           # post-readability/trafilatura extraction (boilerplate stripped)
  meta.json               # {title, byline, site_name, published, modified, lang,
                          #  description, canonical, og:*, jsonld[], word_count}
  assets/                 # inlined images referenced by readable.html, renamed deterministically
  content.raw.md          # pandoc/trafilatura output, no post-processing
  content.linted.md       # after `rumdl check --fix` (+ a normalization pass: ATX headings,
                          #  fenced code, reference-style → inline links, collapse >2 blank lines)
  lint.report.txt         # remaining rumdl violations after --fix (what the agent must handle)
  final.md                # copy of content.linted.md — THIS is what the agent edits
  a2m.json                # manifest: engine used, versions, stage timings, checksums,
                          #  a "stages_completed" list so resume is trivial
```

### Pipeline stages (each idempotent, each writes one or more files above)

1. `fetch` — `curl`/`httpx` by default; `--render` switches to a headless browser (Playwright) for JS-heavy sites. Store raw bytes + headers + final URL.
2. `extract` — run readability/trafilatura on `raw.html` to get `readable.html` and `meta.json`. Download referenced images into `assets/` and rewrite src paths.
3. `convert` — `pandoc -f html -t gfm --wrap=none` (or trafilatura's markdown output) → `content.raw.md`. `--wrap=none` is important: wrapping is the agent's call, not the converter's.
4. `lint` — `rumdl check --fix content.raw.md > content.linted.md`, then rerun `rumdl check` and save remaining violations to `lint.report.txt`. Also normalize: ensure one H1, demote all headings so the document has a single top-level title, strip tracking query params from links.
5. `finalize` — copy `content.linted.md` → `final.md`, write `a2m.json` manifest.

### Skill (`a2m`) instructions to the agent, after the CLI has run

- Read `final.md` first. This is your editing target.
- Read `meta.json` — title/author/date go in frontmatter or an H1 + byline block.
- Read `lint.report.txt` — fix every remaining violation (they are things `--fix` couldn't auto-resolve, e.g. ambiguous list nesting).
- **If anything in `final.md` looks wrong or suspicious, diff against `readable.html` and `raw.html` before editing.** Those files are the source of truth; never invent content that isn't in them.
- Do NOT re-fetch the URL. If you think you need to, the CLI failed — report it instead.
- Do not paraphrase prose for stylistic reasons. The only edits allowed are: (a) fix converter artifacts, (b) restructure for markdown readability (heading depth, code fence languages, table formatting), (c) apply lint fixes. Content must match the source.
- When done, overwrite `final.md` and optionally copy it to the user-requested destination.

### Why this split matters for correctness: the agent can cheaply `grep raw.html` for any string it's unsure about, so "did the converter drop this code block?" becomes a 1-second check instead of a re-fetch + re-extract round trip

### Nice-to-haves (v2)

- `a2m diff <workspace>` — word-level diff between `final.md` and a plain-text projection of `raw.html`, to catch silent content loss.
- `--engine` fallback chain: try pandoc, fall back to trafilatura if pandoc output is empty or loses >X% of the word count.
- Per-site adapters for known-tricky sources (Substack, Medium, Notion public pages).

## Impact

For the task I just did:

- Zero risk of the small model silently dropping a code example — extraction is deterministic and the raw HTML is on disk for cross-checking.
- ~1 WebFetch call saved (no re-fetch to double-check), plus a large chunk of hand-typing replaced by a `rumdl --fix` pass.
- The agent's role shrinks to "polish + verify," which is exactly what LLMs are good at and exactly where the rest of the pipeline is weak.
- Reproducible: re-running `a2m <url>` on the same workspace is a no-op; re-running with `--force` gives a byte-identical `raw.html` assuming the server hasn't changed, so regressions in the converter are easy to bisect.
- Generalizes cleanly to the common "save this article as markdown for my notes" request without me reinventing the pipeline each time.
