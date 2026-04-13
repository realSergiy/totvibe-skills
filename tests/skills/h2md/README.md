# h2md test suite

Black-box tests. Assert on final outputs (`article.md`, `meta.json`, `notes.md`), not internals.

## Rules

1. Use the `pipeline` fixture: HTML in, final outputs out. Don't call internal functions.
2. Don't import or construct `BeautifulSoup`. Don't read intermediate files (`article.raw.md`, `article.prelint.md`, `raw.headers.json`).
3. Organize tests by behavior (extraction, code blocks, tabs, metadata, detection), not pipeline stage.
4. Exception: `test_language_sniffing.py` tests `_sniff_language` directly as a stable contract — too many edge cases to cover end-to-end efficiently.

## Why

So the implementation can be refactored freely without tests causing false positives, as long as the same HTML produces equivalent markdown, metadata, and issue notes.
