#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "httpx>=0.28",
#     "beautifulsoup4>=4.13",
#     "lxml>=5.0",
#     "readability-lxml>=0.8",
#     "markdownify>=0.14",
#     "typer>=0.15",
#     "toon-format>=0.9.0b1",
# ]
# ///
"""Convert web articles to clean, faithful markdown."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Annotated
from urllib.parse import urlparse

import httpx
import typer
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from markdownify import MarkdownConverter
from readability import Document
from toon_format import encode

__version__ = "0.1.0"

app = typer.Typer()

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "h2md"
DEFAULT_LINT_CMD = "rumdl check --fix"
USER_AGENT = "Mozilla/5.0 (compatible; h2md/0.1; +https://github.com/totvibe/skills)"

STRIP_TAGS = {"script", "style", "button", "svg", "nav", "footer", "header", "noscript"}
INLINE_TAGS = {"span", "a", "em", "strong", "b", "i", "code", "abbr", "time", "small", "sub", "sup"}

STAGES = ["fetch", "extract", "metadata", "assets", "convert", "normalize", "lint", "detect"]


@dataclass
class Manifest:
    url: str
    stages_completed: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    checksums: dict[str, str] = field(default_factory=dict)
    version: str = __version__

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({
            "url": self.url,
            "stages_completed": self.stages_completed,
            "timings": self.timings,
            "checksums": self.checksums,
            "version": self.version,
        }, indent=2) + "\n")

    @classmethod
    def load(cls, path: Path) -> Manifest:
        data = json.loads(path.read_text())
        return cls(
            url=data["url"],
            stages_completed=data.get("stages_completed", []),
            timings=data.get("timings", {}),
            checksums=data.get("checksums", {}),
            version=data.get("version", __version__),
        )

    def stage_done(self, name: str) -> bool:
        return name in self.stages_completed

    def mark_done(self, name: str, elapsed: float, **checksums: str) -> None:
        if name not in self.stages_completed:
            self.stages_completed.append(name)
        self.timings[name] = round(elapsed, 3)
        self.checksums.update(checksums)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _url_to_slug(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "").replace(".", "_")
    path = parsed.path.strip("/").replace("/", "_")
    slug = f"{host}_{path}" if path else host
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", slug)
    return slug[:80]


# ---------------------------------------------------------------------------
# Stage 1: Fetch
# ---------------------------------------------------------------------------

def _fetch(workspace: Path, manifest: Manifest, url: str, force: bool) -> bool:
    if not force and manifest.stage_done("fetch"):
        return True
    t0 = time.monotonic()
    with httpx.Client(follow_redirects=True, timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.get(url)
        resp.raise_for_status()
    raw_bytes = resp.content
    (workspace / "source.url").write_text(url + "\n")
    (workspace / "raw.html").write_bytes(raw_bytes)
    headers_data = {
        "status_code": resp.status_code,
        "final_url": str(resp.url),
        "headers": dict(resp.headers),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    (workspace / "raw.headers.json").write_text(json.dumps(headers_data, indent=2) + "\n")
    elapsed = time.monotonic() - t0
    manifest.mark_done("fetch", elapsed, raw_html=_sha256(raw_bytes))
    return True


# ---------------------------------------------------------------------------
# Stage 2: Extract (structural preprocessing + article extraction)
# ---------------------------------------------------------------------------

def _insert_span_whitespace(tag: Tag) -> None:
    for child in list(tag.descendants):
        if not isinstance(child, Tag) or child.name not in INLINE_TAGS:
            continue
        prev = child.previous_sibling
        if isinstance(prev, Tag) and prev.name in INLINE_TAGS:
            prev_text = prev.get_text()
            curr_text = child.get_text()
            if prev_text and curr_text and not prev_text.endswith((" ", "\n")) and not curr_text.startswith((" ", "\n")):
                child.insert_before(" ")
        elif isinstance(prev, NavigableString):
            text = str(prev)
            if text and not text.endswith((" ", "\n")):
                nxt_text = child.get_text()
                if nxt_text and not nxt_text.startswith((" ", "\n")):
                    pass


def _flatten_tablists(soup: BeautifulSoup) -> None:
    for tablist in soup.find_all(attrs={"role": "tablist"}):
        tab_elements = tablist.find_all(attrs={"role": "tab"})
        labels = [t.get_text(strip=True) for t in tab_elements]
        panel_ids = [t.get("aria-controls", "") for t in tab_elements]

        panels: list[Tag | None] = []
        for pid in panel_ids:
            if pid:
                panel = soup.find(id=pid)
                if panel and isinstance(panel, Tag):
                    panels.append(panel)
                    continue
            panels.append(None)

        if not panels or all(p is None for p in panels):
            siblings = []
            node = tablist.next_sibling
            while node:
                if isinstance(node, Tag) and node.get("role") == "tabpanel":
                    siblings.append(node)
                node = node.next_sibling if node else None
            panels = siblings + [None] * (len(labels) - len(siblings))

        replacement = soup.new_tag("div", attrs={"class": "h2md-flattened-tabs"})
        for label, panel in zip(labels, panels):
            if not panel:
                continue
            heading = soup.new_tag("h4")
            heading.string = label
            replacement.append(heading)
            for child in list(panel.children):
                if isinstance(child, Tag):
                    replacement.append(child.extract())
                elif isinstance(child, NavigableString) and child.strip():
                    replacement.append(child.extract())

        tablist.replace_with(replacement)
        for panel in panels:
            if panel and isinstance(panel, Tag) and panel.parent:
                panel.decompose()


def _reconstruct_terminal_regions(soup: BeautifulSoup) -> None:
    terminal_keywords = {"terminal", "output", "console", "command", "shell"}
    for region in soup.find_all(attrs={"role": "region"}):
        aria_label = str(region.get("aria-label") or "").lower()
        if not any(kw in aria_label for kw in terminal_keywords):
            continue
        texts = []
        for el in region.descendants:
            if isinstance(el, NavigableString):
                text = str(el).strip()
                if text:
                    texts.append(text)
        if texts:
            pre = soup.new_tag("pre")
            code = soup.new_tag("code", attrs={"class": "language-text"})
            code.string = " ".join(texts)
            pre.append(code)
            region.replace_with(pre)


def _preprocess_dom(soup: BeautifulSoup) -> BeautifulSoup:
    _flatten_tablists(soup)
    _reconstruct_terminal_regions(soup)

    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(attrs={"role": "button"}):
        if isinstance(tag, Tag):
            tag.decompose()

    _insert_span_whitespace(soup)
    return soup


def _extract_article(soup: BeautifulSoup, raw_html: str, selector: str | None) -> str:
    if selector:
        el = soup.select_one(selector)
        if el:
            return str(el)

    article = soup.find("article")
    if article and isinstance(article, Tag):
        text = article.get_text(strip=True)
        if len(text) > 100:
            return str(article)

    main = soup.find("main")
    if main and isinstance(main, Tag):
        text = main.get_text(strip=True)
        if len(text) > 100:
            return str(main)

    doc = Document(raw_html)
    summary = doc.summary()
    if summary and len(BeautifulSoup(summary, "lxml").get_text(strip=True)) > 100:
        return summary

    best = None
    best_len = 0
    for div in soup.find_all("div"):
        if isinstance(div, Tag):
            p_count = len(div.find_all("p", recursive=False))
            text_len = len(div.get_text(strip=True))
            score = p_count * 100 + text_len
            if score > best_len:
                best_len = score
                best = div
    if best:
        return str(best)

    return str(soup.body) if soup.body else str(soup)


def _extract(workspace: Path, manifest: Manifest, force: bool, selector: str | None) -> bool:
    if not force and manifest.stage_done("extract"):
        return True
    t0 = time.monotonic()
    raw_html = (workspace / "raw.html").read_text(errors="replace")
    soup = BeautifulSoup(raw_html, "lxml")
    soup = _preprocess_dom(soup)
    article_html = _extract_article(soup, raw_html, selector)
    (workspace / "article.html").write_text(article_html)
    elapsed = time.monotonic() - t0
    manifest.mark_done("extract", elapsed, article_html=_sha256(article_html.encode()))
    return True


# ---------------------------------------------------------------------------
# Stage 3: Metadata
# ---------------------------------------------------------------------------

def _parse_jsonld(soup: BeautifulSoup) -> dict:
    meta: dict = {}
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, list):
            data = next((d for d in data if d.get("@type") in ("Article", "BlogPosting", "NewsArticle", "TechArticle")), {})
        if data.get("@type") in ("Article", "BlogPosting", "NewsArticle", "TechArticle"):
            meta["title"] = meta.get("title") or data.get("headline")
            author = data.get("author")
            if isinstance(author, dict):
                meta["author"] = author.get("name")
            elif isinstance(author, list) and author:
                names = [a.get("name", str(a)) if isinstance(a, dict) else str(a) for a in author]
                meta["author"] = ", ".join(n for n in names if n)
            meta["date"] = meta.get("date") or data.get("datePublished")
            meta["description"] = meta.get("description") or data.get("description")
            meta["canonical_url"] = meta.get("canonical_url") or data.get("url")
    return meta


def _parse_og(soup: BeautifulSoup) -> dict:
    meta: dict = {}
    og_map = {
        "og:title": "title",
        "og:description": "description",
        "og:url": "canonical_url",
        "og:image": "og_image",
        "og:site_name": "site_name",
        "og:locale": "lang",
        "article:author": "author",
        "article:published_time": "date",
    }
    for tag in soup.find_all("meta"):
        prop = str(tag.get("property", ""))
        content = str(tag.get("content", ""))
        if prop in og_map and content:
            meta.setdefault(og_map[prop], content)
    return meta


def _parse_twitter(soup: BeautifulSoup) -> dict:
    meta: dict = {}
    tw_map = {"twitter:title": "title", "twitter:description": "description", "twitter:image": "og_image"}
    for tag in soup.find_all("meta"):
        name = str(tag.get("name", ""))
        content = str(tag.get("content", ""))
        if name in tw_map and content:
            meta.setdefault(tw_map[name], content)
    return meta


def _parse_html_meta(soup: BeautifulSoup) -> dict:
    meta: dict = {}
    title_tag = soup.find("title")
    if title_tag:
        meta["title"] = title_tag.get_text(strip=True)
    for tag in soup.find_all("meta"):
        name = str(tag.get("name") or "").lower()
        content = str(tag.get("content", ""))
        if name == "author" and content:
            meta.setdefault("author", content)
        elif name == "description" and content:
            meta.setdefault("description", content)
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical and isinstance(canonical, Tag):
        meta.setdefault("canonical_url", str(canonical.get("href", "")))
    lang_tag = soup.find("html")
    if lang_tag and isinstance(lang_tag, Tag):
        lang = lang_tag.get("lang")
        if lang:
            meta["lang"] = lang
    return meta


def _metadata(workspace: Path, manifest: Manifest, force: bool) -> bool:
    if not force and manifest.stage_done("metadata"):
        return True
    t0 = time.monotonic()
    raw_html = (workspace / "raw.html").read_text(errors="replace")
    soup = BeautifulSoup(raw_html, "lxml")

    meta: dict = {}
    for parser in [_parse_jsonld, _parse_og, _parse_twitter, _parse_html_meta]:
        for k, v in parser(soup).items():
            meta.setdefault(k, v)

    article_html = (workspace / "article.html").read_text(errors="replace")
    article_text = BeautifulSoup(article_html, "lxml").get_text(" ", strip=True)
    words = len(article_text.split())
    meta["word_count"] = words
    meta["reading_time_minutes"] = max(1, round(words / 250))

    (workspace / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    elapsed = time.monotonic() - t0
    manifest.mark_done("metadata", elapsed)
    return True


# ---------------------------------------------------------------------------
# Stage 4: Assets
# ---------------------------------------------------------------------------

def _assets(workspace: Path, manifest: Manifest, force: bool, no_assets: bool) -> bool:
    if no_assets:
        if "assets" not in manifest.stages_completed:
            manifest.mark_done("assets", 0.0)
        return True
    if not force and manifest.stage_done("assets"):
        return True
    t0 = time.monotonic()
    article_path = workspace / "article.html"
    html = article_path.read_text(errors="replace")
    soup = BeautifulSoup(html, "lxml")
    imgs = soup.find_all("img")
    if not imgs:
        manifest.mark_done("assets", time.monotonic() - t0)
        return True

    assets_dir = workspace / "assets"
    assets_dir.mkdir(exist_ok=True)
    downloaded = 0

    with httpx.Client(follow_redirects=True, timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        for img in imgs:
            src = str(img.get("src", ""))
            if not src or src.startswith("data:"):
                continue
            try:
                resp = client.get(src)
                resp.raise_for_status()
            except (httpx.HTTPError, httpx.InvalidURL):
                continue
            ext = Path(urlparse(src).path).suffix or ".bin"
            filename = _sha256(src.encode())[:12] + ext
            (assets_dir / filename).write_bytes(resp.content)
            img["src"] = f"assets/{filename}"
            downloaded += 1

    if downloaded:
        article_path.write_text(str(soup))

    elapsed = time.monotonic() - t0
    manifest.mark_done("assets", elapsed)
    return True


# ---------------------------------------------------------------------------
# Stage 5: Convert (HTML -> Markdown)
# ---------------------------------------------------------------------------

LANG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^\[[\w.-]+\]", re.MULTILINE), "toml"),
    (re.compile(r"^(curl|bun|npm|npx|docker|brew|apt|pip|yarn|pnpm|deno)\b", re.MULTILINE), "bash"),
    (re.compile(r"^\s*[\[{]"), "json"),
    (re.compile(r"<[A-Z][a-zA-Z]*[\s/>]"), "tsx"),
    (re.compile(r"^(def |class |import |from \w+ import )", re.MULTILINE), "python"),
    (re.compile(r"(function\s|const\s|let\s|=>|module\.exports)"), "javascript"),
    (re.compile(r"^(html|body|div|span|\.|#|@media)\s*\{", re.MULTILINE), "css"),
]


def _sniff_language(code: str) -> str:
    code = code.strip()
    if not code:
        return "text"
    for pattern, lang in LANG_PATTERNS:
        if pattern.search(code):
            return lang
    return "text"


def _classes_from_tag(tag: Tag) -> list[str]:
    raw = tag.get("class")
    if raw is None:
        return []
    if isinstance(raw, str):
        return raw.split()
    return [str(c) for c in raw]


def _code_language_callback(el: Tag) -> str:
    candidates = [el]
    code_child = el.find("code")
    if code_child and isinstance(code_child, Tag):
        candidates.insert(0, code_child)
    for tag in candidates:
        for cls in _classes_from_tag(tag):
            for prefix in ("language-", "lang-", "highlight-"):
                if cls.startswith(prefix):
                    lang = cls[len(prefix):]
                    if lang and lang != "text":
                        return lang
    code = el.get_text()
    return _sniff_language(code)


class H2mdConverter(MarkdownConverter):
    pass


def _convert(workspace: Path, manifest: Manifest, force: bool) -> bool:
    if not force and manifest.stage_done("convert"):
        return True
    t0 = time.monotonic()
    article_html = (workspace / "article.html").read_text(errors="replace")
    converter = H2mdConverter(
        heading_style="ATX",
        code_language="text",
        code_language_callback=_code_language_callback,
        strip=["button", "svg", "nav"],
        escape_misc=False,
    )
    md = converter.convert(article_html)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip() + "\n"
    (workspace / "article.raw.md").write_text(md)
    elapsed = time.monotonic() - t0
    manifest.mark_done("convert", elapsed)
    return True


# ---------------------------------------------------------------------------
# Stage 6: Normalize (pre-lint fixes)
# ---------------------------------------------------------------------------

_BOLD_HEADING_RE = re.compile(r"^\*\*([A-Z][^*]{3,80})\*\*$")
_EMPTY_FENCE_RE = re.compile(r"```[a-z]*\n\s*\n?```", re.MULTILINE)


def _normalize(workspace: Path, manifest: Manifest, force: bool) -> bool:
    if not force and manifest.stage_done("normalize"):
        return True
    t0 = time.monotonic()
    md = (workspace / "article.raw.md").read_text()
    meta_path = workspace / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    frontmatter_lines = ["---"]
    if meta.get("title"):
        safe_title = meta["title"].replace('"', '\\"')
        frontmatter_lines.append(f'title: "{safe_title}"')
    if meta.get("author"):
        frontmatter_lines.append(f'author: "{meta["author"]}"')
    if meta.get("date"):
        frontmatter_lines.append(f'date: "{meta["date"]}"')
    if meta.get("canonical_url"):
        frontmatter_lines.append(f'source: "{meta["canonical_url"]}"')
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    md = _EMPTY_FENCE_RE.sub("", md)

    lines = md.split("\n")
    normalized: list[str] = []
    for line in lines:
        m = _BOLD_HEADING_RE.match(line.strip())
        if m:
            normalized.append(f"#### {m.group(1)}")
        else:
            normalized.append(line.rstrip())
    md = "\n".join(normalized)

    content_lines = md.lstrip().split("\n")
    first_content = next((ln for ln in content_lines if ln.strip()), "")
    if not first_content.startswith("# ") and meta.get("title"):
        md = f"# {meta['title']}\n\n{md}"

    md = re.sub(r"\n{3,}", "\n\n", md)
    md = frontmatter + "\n\n" + md.strip() + "\n"

    (workspace / "article.prelint.md").write_text(md)
    elapsed = time.monotonic() - t0
    manifest.mark_done("normalize", elapsed)
    return True


# ---------------------------------------------------------------------------
# Stage 7: Lint
# ---------------------------------------------------------------------------

def _lint(workspace: Path, manifest: Manifest, force: bool, lint_cmd: str) -> bool:
    if not force and manifest.stage_done("lint"):
        return True
    t0 = time.monotonic()
    prelint = workspace / "article.prelint.md"
    article = workspace / "article.md"
    shutil.copy2(prelint, article)

    lint_parts = lint_cmd.split()
    lint_exe = lint_parts[0] if lint_parts else "rumdl"

    if not shutil.which(lint_exe):
        (workspace / "lint.report.txt").write_text(f"{lint_exe} not found on PATH, skipping lint\n")
        manifest.mark_done("lint", time.monotonic() - t0)
        return True

    subprocess.run([*lint_parts, str(article)], capture_output=True, text=True)

    check_cmd = [lint_exe, "check", str(article)]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    (workspace / "lint.report.txt").write_text(result.stdout + result.stderr)

    elapsed = time.monotonic() - t0
    manifest.mark_done("lint", elapsed)
    return True


# ---------------------------------------------------------------------------
# Stage 8: Detect artifacts
# ---------------------------------------------------------------------------

_FUSED_RE = re.compile(r"\S{50,}")
_HTML_LEAK_RE = re.compile(r"<(svg|button|input|form)\b|role=[\"']")
_EMPTY_BLOCK_RE = re.compile(r"```[a-z]*\n\s*\n?```")
_TAB_LABEL_RE = re.compile(r"^[a-z]{2,15}$", re.IGNORECASE)


def _context_around(text: str, start: int, end: int, ctx: int = 40) -> str:
    s = max(0, start - ctx)
    e = min(len(text), end + ctx)
    return text[s:e].replace("\n", "\\n")


def _detect(workspace: Path, manifest: Manifest, force: bool) -> bool:
    if not force and manifest.stage_done("detect"):
        return True
    t0 = time.monotonic()
    article = workspace / "article.md"
    if not article.exists():
        manifest.mark_done("detect", time.monotonic() - t0)
        return True
    md = article.read_text()
    issues: list[str] = []

    for m in _FUSED_RE.finditer(md):
        ctx = _context_around(md, m.start(), m.end())
        issues.append(f"## Likely fused text\n**Find:** `{ctx}`\n**Source check:** article.html\n**Suggested fix:** verify whitespace between tokens\n")

    for m in _HTML_LEAK_RE.finditer(md):
        ctx = _context_around(md, m.start(), m.end())
        issues.append(f"## HTML leakage\n**Find:** `{ctx}`\n**Source check:** article.html\n**Suggested fix:** remove or convert to markdown\n")

    for m in _EMPTY_BLOCK_RE.finditer(md):
        ctx = _context_around(md, m.start(), m.end(), 20)
        issues.append(f"## Empty code block\n**Find:** `{ctx}`\n**Suggested fix:** remove empty fence\n")

    lines = md.split("\n")
    for i, line in enumerate(lines[:-1]):
        if _TAB_LABEL_RE.match(line.strip()) and i + 1 < len(lines) and lines[i + 1].strip().startswith("```"):
            ctx = f"{line.strip()}\\n{lines[i+1].strip()}"
            issues.append(f"## Suspicious tab label\n**Find:** `{ctx}`\n**Suggested fix:** merge as prose prefix or remove\n")

    notes = "\n".join(issues) if issues else ""
    (workspace / "notes.md").write_text(notes)
    elapsed = time.monotonic() - t0
    manifest.mark_done("detect", elapsed)
    return True


# ---------------------------------------------------------------------------
# Stage 9: Handoff
# ---------------------------------------------------------------------------

def _handoff(workspace: Path, manifest: Manifest, url: str) -> None:
    meta_path = workspace / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    notes_path = workspace / "notes.md"
    notes_text = notes_path.read_text() if notes_path.exists() else ""
    issue_count = notes_text.count("## ") if notes_text.strip() else 0
    lint_path = workspace / "lint.report.txt"
    lint_text = lint_path.read_text() if lint_path.exists() else ""
    lint_remaining = len([ln for ln in lint_text.strip().split("\n") if ln.strip() and "not found" not in ln.lower()])

    output = {
        "h2md": {
            "url": url,
            "workspace": str(workspace),
            "article": "article.md",
            "words": meta.get("word_count", 0),
            "issues": issue_count,
            "lint_remaining": lint_remaining,
        },
        "next": "Read notes.md for known issues. Edit article.md to fix. Cross-reference article.html for fidelity. Do not re-download.",
    }
    print(encode(output))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _version_callback(value: bool) -> None:
    if value:
        print(f"h2md {__version__}")
        raise typer.Exit


@app.command()
def main(
    url: Annotated[str, typer.Argument(help="URL of the article to convert")],
    out: Annotated[Path | None, typer.Option("--out", help="Workspace directory")] = None,
    force: Annotated[bool, typer.Option("--force", help="Re-run all stages")] = False,
    no_assets: Annotated[bool, typer.Option("--no-assets", help="Skip image download")] = False,
    js: Annotated[bool, typer.Option("--js", help="JS rendering (requires playwright)")] = False,
    lint_cmd: Annotated[str, typer.Option("--lint", help="Lint command")] = DEFAULT_LINT_CMD,
    selector: Annotated[str | None, typer.Option("--selector", help="CSS selector for extraction")] = None,
    version: Annotated[bool | None, typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version")] = None,
) -> None:
    """Convert a web article to clean, faithful markdown."""
    if js:
        raise typer.BadParameter("JS rendering requires playwright which is not installed")

    workspace = out or (DEFAULT_CACHE_DIR / _url_to_slug(url))
    workspace.mkdir(parents=True, exist_ok=True)

    manifest_path = workspace / "h2md.json"
    if manifest_path.exists() and not force:
        manifest = Manifest.load(manifest_path)
    else:
        manifest = Manifest(url=url)

    if force:
        manifest.stages_completed.clear()

    stage_fns: list[tuple[str, Callable[[], bool]]] = [
        ("fetch", lambda: _fetch(workspace, manifest, url, force)),
        ("extract", lambda: _extract(workspace, manifest, force, selector)),
        ("metadata", lambda: _metadata(workspace, manifest, force)),
        ("assets", lambda: _assets(workspace, manifest, force, no_assets)),
        ("convert", lambda: _convert(workspace, manifest, force)),
        ("normalize", lambda: _normalize(workspace, manifest, force)),
        ("lint", lambda: _lint(workspace, manifest, force, lint_cmd)),
        ("detect", lambda: _detect(workspace, manifest, force)),
    ]

    for name, fn in stage_fns:
        try:
            fn()
        except Exception as exc:
            manifest.save(manifest_path)
            typer.echo(f"Stage '{name}' failed: {exc}", err=True)
            raise typer.Exit(1)
        manifest.save(manifest_path)

    _handoff(workspace, manifest, url)


if __name__ == "__main__":
    app()
