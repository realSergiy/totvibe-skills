# a2m follow-up: lessons from the cleanup phase

## Context

Follow-up to the initial a2m suggestion. After filing that, I actually did the manual cleanup pass on `bun/bun1_3.md` and hit several new issues that the first suggestion didn't cover. These are all things a better pipeline would handle automatically — filing them so they're on the record.

## Gap — what broke during the LLM polish phase

### 1. Edit calls failed because rumdl silently rewrote the file between Read and Edit

I read the file, constructed an Edit with the exact text I saw, and it failed with "String to replace not found." Cause: rumdl had auto-wrapped a bare URL in `<...>` angle brackets and that had concatenated with adjacent text (because the fused-terminal line had no space before the URL), so the on-disk bytes no longer matched what I'd just read. I had to `python3 -c "...repr..."` the raw bytes to see what was actually there. This is a generic problem — any tool that rewrites the file between fetch and polish invalidates the agent's cached view.

### 2. The root cause of all fused-terminal/tab-label garbage is identifiable in the source HTML

When I went back to `raw.html` to reconstruct the fused terminal output, the original HTML had **semantic ARIA labels** on every component: `aria-label="Bun development server terminal output"`, `aria-label="Command line input"`, `aria-label="Server status"`, `aria-label="Local server URL"`. A naive HTML→MD converter concatenates span text with no separators and produces `Bunv1.3.12ready in6.62ms`. A smart converter that respects `role="region"`, `aria-label`, and adjacent-span boundaries could reconstruct `Bun v1.3.12 ready in 6.62 ms` deterministically. Same for the install-tabs `role="tablist"` — bare labels like `powershell`/`npm`/`brew`/`docker` between code blocks are the *obvious* fingerprint of a tab component that got flattened without preserving the tab-label → tab-panel relationship.

### 3. Rumdl caught things my ad-hoc cleanup missed

Even after my manual pass, `rumdl check` found:

- **MD041** — first line wasn't an H1 (the page's `<title>` / og:title was never used as a document title)
- **MD036** — 2x "bold line used as heading" (`**RFC 6455 Compliant Subprotocol Negotiation**`)
- **MD036** — italicized testimonial `*"...quote..."* — Ahmad Nassri, CTO of Socket` that should have been a `>` blockquote

All three are deterministic patterns the converter could handle.

### 4. Language detection was `text` for everything

Every code block came out as ```` ```text ```` even when the content was obviously TOML (`[install]\nlinker = "hoisted"`) or bash. The original HTML had `class="language-*"` in places and was detectable by content sniffing elsewhere.

### 5. Empty code blocks are a downstream symptom of tab-label stripping

I found `` ``` `` / empty / `` ``` `` pairs left behind when the tab-label text was removed but the fence wasn't. The converter should drop the fence when its body becomes empty after label extraction.

### 6. NOTES.md with line numbers is wrong — edits drift lines

If a2m's artifact-detection report says "fused terminal at line 52," by the time the agent fixes issue #1 the line number for #2 is stale. Anchors should be *stable substrings* the agent can Edit-match against, not coordinates.

## Responsibility

All six are pattern-matchable at conversion time against structural signals that already exist in the source HTML (ARIA roles, class names, tag adjacency) or in well-known markdown anti-patterns. The LLM polish phase should handle *judgment calls* (wording, section ordering, TL;DR), not mechanical recovery from a lossy converter.

## Suggestion

Extensions to the a2m pipeline proposed in the earlier suggestion:

### A. Structural HTML extractor, not just tag-stripping

Before converting, walk the DOM and recognize known UI components:

- `role="tablist"` + `role="tabpanel"` → flatten to one code block with `# <tab label>` comment sections (or separate blocks under `#### <label>` headings)
- `role="region"` with `aria-label` containing "terminal" / "output" / "console" → reconstruct as a code block, inserting whitespace at *every* span boundary (the original rendering relied on CSS margins that evaporate in plain text)
- Copy-buttons, SVG icons, `<script>` tags → strip before text extraction, not during
- `<blockquote>` or a long italicized `<p>` immediately followed by an em-dash attribution line → emit as `>` blockquote with `> — Author` attribution line

### B. Deterministic lint-preemption pass, run before rumdl

Between "convert" and "lint," run a pass that preempts common rumdl violations:

- **MD041**: if the first non-blank line isn't an H1, synthesize one from `meta.json.title` (which a2m already has from step 3 of the original pipeline)
- **MD036**: any line matching `^\*\*[A-Z][^*]{3,80}\*\*$` alone on a paragraph → promote to `####` heading at current depth
- Empty code fences (` ``` ` / blank / ` ``` `) → drop
- Bare label lines immediately before a code fence (single-word, short, no punctuation) → merge as prose prefix: "In `<label>`:"

### C. Post-lint freeze + exact-quote NOTES.md

After rumdl runs, re-read the file and generate `NOTES.md` with issues keyed by **exact substring** (7-15 words of context) from the *post-lint* file, not line numbers. Example entry:

```markdown
## Likely fused terminal output
**Find:** `directly with Bun:\n\n```text\n❯ bun './**/*.html'`
**Check against:** `article.html` line 1432 — original ARIA region had 7 spans
**Suggested fix:** verify whitespace between `Bun`, `v1.3.12`, `ready in`, `6.62`, `ms`
```

This makes the polish phase a series of targeted Edits against stable anchors.

### D. Language inference for code fences

If the HTML has `class="language-X"`, use it. Otherwise sniff content:

- `^\[[\w-]+\]$` on first line → `toml`
- `^(curl|bun|npm|docker|brew|powershell)` → `bash` (or `powershell`)
- `^{` / `^\[` → `json`
- React/JSX (`<[A-Z]`) → `tsx`
- Fall back to `text` only if no signal

### E. Pre-lint snapshot for diffing

Keep `article.md` (post-lint) and `article.prelint.md` (converter output) side by side. When the polish agent hits an Edit mismatch it can't explain, it has `diff article.prelint.md article.md` to see what rumdl did. (Original suggestion mentioned `article.raw.md` but didn't spell out that rumdl's rewrites are the #1 cause of Edit cache invalidation.)

## Impact

- Eliminates most of the polish phase entirely: tabs, terminal blocks, and testimonials come out correct at conversion time.
- Eliminates the Edit-cache-invalidation footgun — the agent's Read matches the on-disk state because the lint pass happens before handoff and exact quotes are preserved in NOTES.md.
- Fewer rumdl failures means fewer polish iterations, which means faster and cheaper runs.
- The structural extractor is where the biggest fidelity wins live — everything downstream is cleanup for problems the extractor created.
