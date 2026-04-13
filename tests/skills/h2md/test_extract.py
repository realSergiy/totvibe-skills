from __future__ import annotations

from bs4 import BeautifulSoup


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def test_strips_script_style(h2md):
    html = "<div><script>alert(1)</script><style>.x{}</style><p>Keep</p></div>"
    soup = _soup(html)
    h2md._preprocess_dom(soup)
    assert soup.find("script") is None
    assert soup.find("style") is None
    assert "Keep" in soup.get_text()


def test_strips_buttons_and_svgs(h2md):
    html = "<div><button>Copy</button><svg><path/></svg><p>Keep</p></div>"
    soup = _soup(html)
    h2md._preprocess_dom(soup)
    assert soup.find("button") is None
    assert soup.find("svg") is None
    assert "Keep" in soup.get_text()


def test_strips_nav_footer_header(h2md):
    html = "<div><nav>Menu</nav><header>Top</header><p>Body</p><footer>Bottom</footer></div>"
    soup = _soup(html)
    h2md._preprocess_dom(soup)
    assert soup.find("nav") is None
    assert soup.find("footer") is None
    assert soup.find("header") is None
    assert "Body" in soup.get_text()


def test_flattens_tablist(h2md, read_fixture):
    html = read_fixture("tabbed_code.html")
    soup = _soup(html)
    h2md._preprocess_dom(soup)
    text = soup.get_text()
    assert soup.find(attrs={"role": "tablist"}) is None
    headings = [h.get_text(strip=True) for h in soup.find_all("h4")]
    assert "curl" in headings
    assert "npm" in headings
    assert "brew" in headings
    assert "curl -fsSL" in text
    assert "npm install" in text
    assert "brew install" in text


def test_reconstructs_terminal_regions(h2md, read_fixture):
    html = read_fixture("terminal_output.html")
    soup = _soup(html)
    h2md._preprocess_dom(soup)
    pre_tags = soup.find_all("pre")
    terminal_texts = [pre.get_text() for pre in pre_tags]
    found = False
    for t in terminal_texts:
        if "Bun" in t and "v1.3.12" in t and "ready in" in t:
            assert "Bun " in t or "Bun v1" in t
            found = True
    assert found, f"Terminal reconstruction not found in: {terminal_texts}"


def test_extract_article_tag(h2md, read_fixture, workspace):
    html = read_fixture("simple_article.html")
    (workspace / "raw.html").write_text(html)
    h2md._extract(workspace, selector=None)
    article_html = (workspace / "article.html").read_text()
    assert "Getting Started with FastAPI" in article_html
    assert "pip install fastapi" in article_html


def test_extract_no_article_tag_uses_fallback(h2md, read_fixture, workspace):
    html = read_fixture("no_article_tag.html")
    (workspace / "raw.html").write_text(html)
    h2md._extract(workspace, selector=None)
    article_html = (workspace / "article.html").read_text()
    assert "Async Patterns" in article_html or "asynchronous" in article_html.lower()


def test_extract_with_selector(h2md, read_fixture, workspace):
    html = read_fixture("no_article_tag.html")
    (workspace / "raw.html").write_text(html)
    h2md._extract(workspace, selector="div.post-body")
    article_html = (workspace / "article.html").read_text()
    assert "Async Patterns" in article_html
    assert "Recent Posts" not in article_html
