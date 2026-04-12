# New skill+CLI: a2m (article-to-markdown)

## Context

User asked me to scrape <https://bun.com/blog/bun-v1.3> and save it as `bun/bun1_3.md`. A common, recurring task — convert a web article to clean markdown for archival / later reading / LLM ingestion.

## Gap

There is no skill for this. My actual workflow was:

1. `WebFetch` — failed: returned a generic AI-summarized blurb (~150 words) instead of the article body. WebFetch's small summarizer model just paraphrases, it does not faithfully extract.
2. `curl -sL` to grab the raw HTML (2017 lines, ~534KB inside `<article>`).
3. Wrote a ~100-line custom Python `HTMLParser` subclass inline in Bash to convert HTML → Markdown (handling h1-h5, p, code, pre with language detection, ul/ol/li with nesting, a/href, blockquote, hr, table/tr/td, strong/em, skipping svg/button/nav/script/style).
4. Second Python pass to clean artifacts: empty anchor links `[]()`, heading-anchor wrappers `[Heading](#anchor)`, collapse `\n{3,}`, strip trailing whitespace.
5. `mkdir -p` + `cp` to final location.
6. Did **not** run `rumdl` (user's preferred markdown linter — I forgot / had no skill prompting me).
7. Did **not** capture any metadata (author, publish date, canonical URL, og:image, reading time).
8. Residual artifacts remained anyway: tab-control fragments concatenated as `curlpowershellnpmbrewdockercurl` on line 1, inline terminal-output fragments fused into prose like `Bun.You can now run HTML files directly with Bun.❯bun './**/*.html'Bunv1.3.12ready in6.62ms→...`, empty code blocks where the tab labels were stripped.

The final file was usable but imperfect, and I had to disclaim the residual artifacts to the user. Re-doing it would mean re-downloading and re-parsing from scratch — none of the intermediate state was saved.

## Responsibility

Article-to-markdown is a deterministic pipeline up until the very last polish step. Asking the LLM to do the whole thing means:

- Burning context on raw HTML or shelling out to write throwaway parsers every time
- Inconsistent results across invocations (different cleanup heuristics each time)
- No caching — re-runs re-download
- Forgetting project conventions (like running `rumdl`)
- WebFetch's summarizer is *actively wrong* for this task because it paraphrases instead of preserving wording, and the user's stated priority is "information should perfectly match the source"

A dedicated tool can do steps 1-6 deterministically, leave a structured workspace on disk, and only hand off to the LLM for the final semantic polish (fixing fused-together text fragments, deciding section order, writing a TL;DR, etc.) — with all intermediate artifacts cached so the polish step is cheap and re-runnable.

## Suggestion

**CLI: `a2m <url> [--out <path>] [--force]`**

Creates a structured workspace (default `~/.cache/a2m/<slug>/` or `./<slug>/` with `--out`), runs the deterministic pipeline, and prints next-step instructions for the LLM agent.

**Workspace layout:**

```text
<slug>/
  raw.html              # original page, untouched (curl/playwright)
  article.html          # extracted <article> / <main> / readability-picked subtree
  meta.json             # title, author, published_at, canonical_url, og:image, lang, site_name, reading_time, word_count
  article.md            # converted markdown (post-rumdl)
  article.raw.md        # pre-rumdl conversion (for diffing if rumdl over-fixes)
  assets/               # downloaded inline images, referenced relatively from article.md
  pipeline.log          # what ran, what flags, exit codes, timings
  NOTES.md              # known artifacts the LLM should review (auto-detected: empty code blocks, suspiciously fused lines, orphaned tab-control text)
```

**Pipeline (deterministic, in order):**

1. **Fetch** — `curl` first; fall back to headless browser (playwright/chromium) if the page is JS-rendered and the `<article>` is empty. Save `raw.html`.
2. **Extract** — try in order: `<article>`, `<main>`, Mozilla Readability (via `readability-lxml` or `@mozilla/readability`), then largest text-density block. Save `article.html`.
3. **Metadata** — parse `<meta>` (OpenGraph, Twitter, Dublin Core), JSON-LD `Article` schema, `<title>`. Save `meta.json`.
4. **Assets** — download referenced `<img src>`, rewrite to relative `assets/` paths.
5. **Convert** — HTML→MD via a real library (`pandoc` if available, else `markdownify` / `html-to-md`) with code-fence language detection from `class="language-*"`. Save `article.raw.md`.
6. **Lint+fix** — run `rumdl check --fix` (configurable: respect `~/.config/a2m/config.toml` for the linter command, defaults to `rumdl`). Save `article.md`.
7. **Artifact detection** — heuristic scan for likely problems: empty fenced blocks, lines with no spaces longer than N chars (fused tokens), `<svg>`/`<button>` text leakage, duplicate consecutive headings, broken links. Write findings to `NOTES.md`.
8. **Print handoff** — to stdout, a one-screen summary: paths, word count, detected issues count, and a suggested next prompt for the agent: "Polish `<slug>/article.md`. Known issues in `NOTES.md`. Source HTML in `article.html` if you need to verify wording. Do NOT re-download."

**Key flags:**

- `--out <path>` — workspace location
- `--force` — re-run even if cached
- `--no-assets` — skip image download
- `--js` — force headless browser
- `--lint <cmd>` — override linter (default `rumdl check --fix`)
- `--print-prompt` — emit only the suggested follow-up prompt (for piping into the next step)

**Skill (`SKILL.md`) responsibilities:**

- Tell the agent: always run `a2m` first; never re-download; read `NOTES.md` before editing; prefer `Edit` over `Write` to preserve the deterministic conversion; cross-reference `article.html` when fixing fused/garbled passages; final output goes wherever the user asked, defaulting to the workspace.
- Document the workspace layout so the agent knows where to look.
- Encode the priority: **wording fidelity > layout fidelity**. Do not paraphrase the source.

### Impact

- This task: ~10 tool calls + custom parser + manual cleanup + apologetic disclaimer → `a2m <url>` + 1-2 surgical `Edit` calls on a pre-linted file with a known-issues checklist.
- Caching makes iteration cheap: if the user says "redo the intro section," the agent re-reads `article.html` instead of re-fetching.
- Eliminates the WebFetch failure mode for article extraction (wrong tool, summarizes instead of extracts).
- Enforces `rumdl` automatically — one less thing to forget.
- Wording-fidelity guarantee aligns with the user's stated priority and is enforced by the pipeline structure (deterministic conversion, LLM only polishes).
