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

import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from collections.abc import Callable
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import httpx
import typer
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from markdownify import MarkdownConverter
from readability import Document
from toon_format import encode

__version__ = "0.3.0"

app = typer.Typer()

DEFAULT_LINT_CMD = "rumdl check --fix"
USER_AGENT = "Mozilla/5.0 (compatible; h2md/0.1; +https://github.com/totvibe/skills)"

STRIP_TAGS = {"script", "style", "button", "svg", "nav", "footer", "header", "noscript"}
INLINE_TAGS = {"span", "a", "em", "strong", "b", "i", "code", "abbr", "time", "small", "sub", "sup"}


# ---------------------------------------------------------------------------
# Stage 1: Fetch
# ---------------------------------------------------------------------------

def _fetch(workspace: Path, url: str) -> None:
    with httpx.Client(follow_redirects=True, timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.get(url)
        resp.raise_for_status()
    (workspace / "source.url").write_text(url + "\n")
    (workspace / "raw.html").write_bytes(resp.content)
    headers_data = {
        "status_code": resp.status_code,
        "final_url": str(resp.url),
        "headers": dict(resp.headers),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    (workspace / "raw.headers.json").write_text(json.dumps(headers_data, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Stage 2: Extract (structural preprocessing + article extraction)
# ---------------------------------------------------------------------------

def _collapse_code_spans(soup: BeautifulSoup) -> None:
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        if not code or not isinstance(code, Tag):
            continue
        if not code.find("span"):
            continue
        text = code.get_text()
        lang_classes = [c for c in _classes_from_tag(code) if c.startswith(("language-", "lang-", "highlight-"))]
        code.clear()
        code.string = text
        if lang_classes:
            code["class"] = " ".join(lang_classes)


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


_TAB_CONTAINER_CLS = {"codetabs", "tabs", "code-tabs", "tabbed-content", "code-group"}
_TAB_BUTTON_CLS = {"codeblocktab", "tabs__item", "tab-button", "tab", "code-group-tab"}
_TAB_PANEL_CLS = {"codeblockcontent", "tabitem", "tab-panel", "tab-content", "tab-pane", "code-group-panel"}


def _has_any_class(tag: Tag, class_set: set[str]) -> bool:
    return any(c.lower() in class_set for c in _classes_from_tag(tag))


def _flatten_class_tabs(soup: BeautifulSoup) -> None:
    for container in soup.find_all(lambda t: isinstance(t, Tag) and _has_any_class(t, _TAB_CONTAINER_CLS)):
        if container.find(attrs={"role": "tablist"}):
            continue

        buttons = container.find_all(lambda t: isinstance(t, Tag) and _has_any_class(t, _TAB_BUTTON_CLS))
        if not buttons:
            all_children = [c for c in container.children if isinstance(c, Tag)]
            nav = next((c for c in all_children if c.name in ("nav", "ul", "div") and not c.find("pre")), None)
            if nav:
                buttons = [c for c in nav.descendants if isinstance(c, Tag) and c.string and c.string.strip()]

        labels = [b.get_text(strip=True) for b in buttons]
        if not labels:
            continue

        panels = container.find_all(lambda t: isinstance(t, Tag) and _has_any_class(t, _TAB_PANEL_CLS))
        if not panels:
            panels = [c for c in container.children if isinstance(c, Tag) and c.find("pre")]

        if not panels:
            continue

        replacement = soup.new_tag("div", attrs={"class": "h2md-flattened-tabs"})
        for label, panel in zip(labels, panels):
            heading = soup.new_tag("h4")
            heading.string = label
            replacement.append(heading)
            for child in list(panel.children):
                if isinstance(child, Tag):
                    replacement.append(child.extract())
                elif isinstance(child, NavigableString) and child.strip():
                    replacement.append(child.extract())

        container.replace_with(replacement)


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


def _clean_code_containers(soup: BeautifulSoup) -> None:
    for pre in soup.find_all("pre"):
        parent = pre.parent
        if not parent or not isinstance(parent, Tag):
            continue
        if parent.name in ("body", "article", "main", "section"):
            continue
        children = [c for c in parent.children if isinstance(c, Tag)]
        if len(children) < 2:
            continue
        for sibling in list(parent.children):
            if sibling is pre or not isinstance(sibling, Tag):
                continue
            if sibling.name in ("code", "pre"):
                continue
            if sibling.find("pre"):
                continue
            sib_text = sibling.get_text(strip=True)
            if not sib_text:
                sibling.decompose()


def _preprocess_dom(soup: BeautifulSoup) -> BeautifulSoup:
    _flatten_tablists(soup)
    _flatten_class_tabs(soup)
    _reconstruct_terminal_regions(soup)

    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(attrs={"role": "button"}):
        if isinstance(tag, Tag):
            tag.decompose()

    _clean_code_containers(soup)
    _collapse_code_spans(soup)
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


def _extract(workspace: Path, selector: str | None) -> None:
    raw_html = (workspace / "raw.html").read_text(errors="replace")
    soup = BeautifulSoup(raw_html, "lxml")
    soup = _preprocess_dom(soup)
    article_html = _extract_article(soup, raw_html, selector)
    (workspace / "article.html").write_text(article_html)


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


def _metadata(workspace: Path) -> None:
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


# ---------------------------------------------------------------------------
# Stage 4: Assets
# ---------------------------------------------------------------------------

def _assets(workspace: Path, no_assets: bool) -> None:
    if no_assets:
        return
    article_path = workspace / "article.html"
    html = article_path.read_text(errors="replace")
    soup = BeautifulSoup(html, "lxml")
    imgs = soup.find_all("img")
    if not imgs:
        return

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
            filename = re.sub(r"[^a-zA-Z0-9]", "_", src)[-40:] + ext
            (assets_dir / filename).write_bytes(resp.content)
            img["src"] = f"assets/{filename}"
            downloaded += 1

    if downloaded:
        article_path.write_text(str(soup))


# ---------------------------------------------------------------------------
# Stage 5: Convert (HTML -> Markdown)
# ---------------------------------------------------------------------------

LANG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^\[[\w.-]+\]", re.MULTILINE), "toml"),
    (re.compile(r"^(curl|bun|npm|npx|docker|brew|apt|pip|yarn|pnpm|deno)\b", re.MULTILINE), "bash"),
    (re.compile(r"^\s*[\[{]"), "json"),
    (re.compile(r"<[A-Z][a-zA-Z]*[\s/>]"), "tsx"),
    (re.compile(r"^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", re.MULTILINE | re.IGNORECASE), "sql"),
    (re.compile(r":\s*(string|number|boolean|void|any)\b|^interface\s|^type\s+\w+\s*=", re.MULTILINE), "typescript"),
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


_KNOWN_LANGS = {
    "javascript", "typescript", "python", "bash", "sh", "shell", "zsh",
    "json", "toml", "yaml", "yml", "html", "css", "scss", "sql",
    "rust", "go", "java", "kotlin", "swift", "ruby", "php", "c", "cpp",
    "tsx", "jsx", "xml", "graphql", "diff", "markdown", "text",
    "powershell", "dockerfile", "makefile", "lua", "perl", "r", "zig",
}

_EXT_TO_LANG = {
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".mts": "typescript", ".tsx": "tsx", ".jsx": "jsx",
    ".py": "python", ".rb": "ruby", ".rs": "rust", ".go": "go",
    ".java": "java", ".kt": "kotlin", ".swift": "swift", ".php": "php",
    ".sh": "bash", ".bash": "bash", ".zsh": "bash",
    ".sql": "sql", ".css": "css", ".scss": "scss", ".html": "html",
    ".json": "json", ".toml": "toml", ".yaml": "yaml", ".yml": "yaml",
    ".xml": "xml", ".md": "markdown", ".c": "c", ".cpp": "cpp", ".h": "c",
}


def _lang_from_data_attrs(el: Tag) -> str | None:
    for tag in [el] + ([el.parent] if el.parent and isinstance(el.parent, Tag) else []):
        for attr in ("data-language", "data-lang"):
            val = str(tag.get(attr, "")).strip().lower()
            if val and val in _KNOWN_LANGS:
                return val
    return None


def _lang_from_siblings(el: Tag) -> str | None:
    parent = el.parent
    if not parent or not isinstance(parent, Tag):
        return None
    for _ in range(2):
        for sibling in parent.children:
            if sibling is el or not isinstance(sibling, Tag):
                continue
            text = sibling.get_text(strip=True).lower()
            if text in _KNOWN_LANGS:
                return text
            for ext, lang in _EXT_TO_LANG.items():
                if text.endswith(ext):
                    return lang
        if parent.parent and isinstance(parent.parent, Tag):
            el = parent
            parent = parent.parent
        else:
            break
    return None


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

    from_data = _lang_from_data_attrs(el)
    if from_data:
        return from_data

    from_sibling = _lang_from_siblings(el)
    if from_sibling:
        return from_sibling

    code = el.get_text()
    return _sniff_language(code)


class H2mdConverter(MarkdownConverter):
    pass


def _convert(workspace: Path) -> None:
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


# ---------------------------------------------------------------------------
# Stage 6: Normalize (pre-lint fixes)
# ---------------------------------------------------------------------------

_BOLD_HEADING_RE = re.compile(r"^\*\*([A-Z][^*]{3,80})\*\*$")
_EMPTY_FENCE_RE = re.compile(r"```[a-z]*\n\s*\n?```", re.MULTILINE)


def _normalize(workspace: Path) -> None:
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


# ---------------------------------------------------------------------------
# Stage 7: Lint
# ---------------------------------------------------------------------------

def _lint(workspace: Path, lint_cmd: str) -> None:
    prelint = workspace / "article.prelint.md"
    article = workspace / "article.md"
    shutil.copy2(prelint, article)

    lint_parts = lint_cmd.split()
    lint_exe = lint_parts[0] if lint_parts else "rumdl"

    if not shutil.which(lint_exe):
        (workspace / "lint.report.txt").write_text(f"{lint_exe} not found on PATH, skipping lint\n")
        return

    subprocess.run([*lint_parts, str(article)], capture_output=True, text=True)

    check_cmd = [lint_exe, "check", str(article)]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    (workspace / "lint.report.txt").write_text(result.stdout + result.stderr)


# ---------------------------------------------------------------------------
# Stage 8: Detect artifacts
# ---------------------------------------------------------------------------

_FUSED_RE = re.compile(r"\S{50,}")
_HTML_LEAK_RE = re.compile(r"<(svg|button|input|form)\b|role=[\"']")
_EMPTY_BLOCK_RE = re.compile(r"```[a-z]*\n\s*\n?```")
_TAB_LABEL_RE = re.compile(r"^[a-z]{2,15}$", re.IGNORECASE)
_FENCE_RE = re.compile(r"^```[^\n]*\n.*?^```", re.MULTILINE | re.DOTALL)
_MD_LINK_URL_RE = re.compile(r"\]\([^\)]+\)")
_INLINE_CODE_RE = re.compile(r"`[^`]+`")


def _exclusion_zones(md: str) -> list[tuple[int, int]]:
    zones: list[tuple[int, int]] = []
    for pattern in (_FENCE_RE, _MD_LINK_URL_RE, _INLINE_CODE_RE):
        for m in pattern.finditer(md):
            zones.append((m.start(), m.end()))
    zones.sort()
    return zones


def _in_exclusion_zone(start: int, end: int, zones: list[tuple[int, int]]) -> bool:
    for zs, ze in zones:
        if zs > end:
            break
        if start < ze and end > zs:
            return True
    return False


def _context_around(text: str, start: int, end: int, ctx: int = 40) -> str:
    s = max(0, start - ctx)
    e = min(len(text), end + ctx)
    return text[s:e].replace("\n", "\\n")


def _detect(workspace: Path) -> None:
    article = workspace / "article.md"
    if not article.exists():
        return
    md = article.read_text()
    issues: list[str] = []
    zones = _exclusion_zones(md)

    for m in _FUSED_RE.finditer(md):
        if _in_exclusion_zone(m.start(), m.end(), zones):
            continue
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


# ---------------------------------------------------------------------------
# Stage 9: Handoff
# ---------------------------------------------------------------------------

def _handoff(workspace: Path, url: str) -> None:
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
        "next": "Read notes.md for known issues. Edit article.md to fix. Cross-reference article.html for fidelity.",
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
    no_assets: Annotated[bool, typer.Option("--no-assets", help="Skip image download")] = False,
    js: Annotated[bool, typer.Option("--js", help="JS rendering (requires playwright)")] = False,
    lint_cmd: Annotated[str, typer.Option("--lint", help="Lint command")] = DEFAULT_LINT_CMD,
    selector: Annotated[str | None, typer.Option("--selector", help="CSS selector for extraction")] = None,
    version: Annotated[bool | None, typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version")] = None,
) -> None:
    """Convert a web article to clean, faithful markdown."""
    if js:
        raise typer.BadParameter("JS rendering requires playwright which is not installed")

    workspace = Path(tempfile.mkdtemp(prefix="h2md_"))

    stages: list[tuple[str, Callable[[], None]]] = [
        ("fetch", lambda: _fetch(workspace, url)),
        ("extract", lambda: _extract(workspace, selector)),
        ("metadata", lambda: _metadata(workspace)),
        ("assets", lambda: _assets(workspace, no_assets)),
        ("convert", lambda: _convert(workspace)),
        ("normalize", lambda: _normalize(workspace)),
        ("lint", lambda: _lint(workspace, lint_cmd)),
        ("detect", lambda: _detect(workspace)),
    ]

    for name, fn in stages:
        try:
            fn()
        except Exception as exc:
            typer.echo(f"Stage '{name}' failed: {exc}", err=True)
            raise typer.Exit(1)

    _handoff(workspace, url)


if __name__ == "__main__":
    app()
