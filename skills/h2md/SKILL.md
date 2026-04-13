---
name: h2md
description: >
  Convert a web article to clean, faithful markdown with metadata extraction, lint fixes, and artifact detection.
  Creates a structured workspace with raw HTML, extracted article, and intermediate files for cheap re-reads and surgical edits.
  Use this whenever you need article content as markdown — blog posts, docs, release notes, changelogs.
  Never manually fetch+parse HTML or use WebFetch for article extraction when h2md is available.
metadata:
  version: "0.3.0"
  user-invocable: "true"
  argument-hint: <url> [--no-assets] [--selector SEL]
---

# h2md -- article-to-markdown converter

`h2md` is a standalone CLI on PATH. Invoke via Bash: `Bash(h2md https://example.com/blog/post)`

Use `h2md` instead of WebFetch or manual HTML parsing for article extraction. WebFetch paraphrases
content through a small summarizer model and loses code blocks, exact wording, and structure.
`h2md` does deterministic extraction preserving every word, code example, and heading from the source.

## Usage

```text
h2md <url>                                # convert article, workspace in /tmp/h2md_*/
h2md <url> --no-assets                    # skip image download
h2md <url> --selector "div.post-body"     # CSS selector override for extraction
h2md <url> --lint "markdownlint --fix"    # override lint command (default: rumdl check --fix)
```

## Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--no-assets` | off | Skip image download |
| `--js` | off | JS rendering (requires playwright) |
| `--lint CMD` | `rumdl check --fix` | Lint command |
| `--selector SEL` | auto-detect | CSS selector for extraction |

## Workspace layout

Each run creates a fresh temporary workspace in `/tmp/h2md_*/`:

```text
<workspace>/
  source.url              # original URL
  raw.html                # exact server response
  raw.headers.json        # response headers, final URL, timestamps
  article.html            # extracted article (post structural preprocessing)
  meta.json               # title, author, date, canonical_url, og_image, word_count
  assets/                 # downloaded images (if not --no-assets)
  article.raw.md          # converter output (pre-normalization)
  article.prelint.md      # post-normalization, pre-rumdl
  article.md              # final output (post-rumdl) — edit this file
  lint.report.txt         # remaining rumdl violations after --fix
  notes.md                # known artifacts with exact-quote anchors
```

## Agent workflow

After `h2md` finishes, follow this workflow to polish the result:

1. **Read `notes.md` first.** It lists known artifacts (fused text, empty blocks, HTML leakage)
   keyed by exact substring anchors you can use with Edit.
2. **Edit `article.md`** to fix issues. Use Edit, not Write — preserve the deterministic
   conversion as the base.
3. **Cross-reference `article.html`** when a passage looks wrong. The extracted HTML is the
   source of truth for wording. Grep it to verify whether text was dropped or garbled.
4. **Do not paraphrase.** Priority is wording fidelity over layout fidelity. Content must
   match the source exactly. Allowed edits: fix converter artifacts, restructure headings,
   correct code fence languages, apply lint fixes.
5. **Run `rumdl check article.md`** after editing to verify no new violations.

## Output

```text
h2md:
  url: https://example.com/blog/post
  workspace: /tmp/h2md_a1b2c3d4
  article: article.md
  words: 3245
  issues: 2
  lint_remaining: 0
next: Read notes.md for known issues. Edit article.md to fix. Cross-reference article.html for fidelity.
```
