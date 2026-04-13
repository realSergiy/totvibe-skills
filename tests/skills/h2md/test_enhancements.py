from __future__ import annotations

from bs4 import BeautifulSoup


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class TestFusedTextExclusions:
    def test_url_in_markdown_link_not_flagged(self, h2md, workspace):
        long_url = "https://github.com/microsoft/TypeScript/pull/62243/files/very-long-path"
        md = f"# Title\n\n[This change was provided]({long_url}) thanks to the work.\n"
        (workspace / "article.md").write_text(md)
        h2md._detect(workspace)
        notes = (workspace / "notes.md").read_text()
        assert "fused text" not in notes.lower()

    def test_long_string_inside_code_fence_not_flagged(self, h2md, workspace):
        long_import = "a" * 60
        md = f"# Title\n\nSome text.\n\n```python\nimport {long_import}\n```\n"
        (workspace / "article.md").write_text(md)
        h2md._detect(workspace)
        notes = (workspace / "notes.md").read_text()
        assert "fused text" not in notes.lower()

    def test_inline_code_not_flagged(self, h2md, workspace):
        long_id = "x" * 60
        md = f"# Title\n\nRun `{long_id}` to start.\n"
        (workspace / "article.md").write_text(md)
        h2md._detect(workspace)
        notes = (workspace / "notes.md").read_text()
        assert "fused text" not in notes.lower()

    def test_real_fused_text_still_flagged(self, h2md, workspace):
        fused = "abcdefghij" * 6
        md = f"# Title\n\nSome text {fused} more text.\n"
        (workspace / "article.md").write_text(md)
        h2md._detect(workspace)
        notes = (workspace / "notes.md").read_text()
        assert "fused text" in notes.lower()

    def test_multiple_links_zero_false_positives(self, h2md, workspace):
        links = " ".join(
            f"[link{i}](https://example.com/very/long/path/to/resource/number/{i})" for i in range(10)
        )
        md = f"# Title\n\nMany links: {links}\n"
        (workspace / "article.md").write_text(md)
        h2md._detect(workspace)
        notes = (workspace / "notes.md").read_text()
        assert "fused text" not in notes.lower()


class TestShikiSpanCollapsing:
    def test_collapses_shiki_spans_to_plain_text(self, h2md):
        html = (
            '<pre class="shiki"><code class="language-javascript">'
            '<span class="token keyword">const</span> '
            '<span class="token variable">x</span>'
            '<span class="token operator">=</span>'
            '<span class="token number">1</span>'
            '<span class="token punctuation">;</span>'
            '</code></pre>'
        )
        soup = _soup(html)
        h2md._collapse_code_spans(soup)
        code = soup.find("code")
        assert code is not None
        assert code.string is not None
        assert "const" in code.string
        assert "<span" not in str(code.string)

    def test_preserves_language_class(self, h2md):
        html = (
            '<pre><code class="language-typescript other-class">'
            '<span class="token">const</span>'
            '</code></pre>'
        )
        soup = _soup(html)
        h2md._collapse_code_spans(soup)
        code = soup.find("code")
        assert code is not None
        classes = str(code.get("class", ""))
        assert "language-typescript" in classes

    def test_no_spans_left_unchanged(self, h2md):
        html = '<pre><code class="language-bash">echo hello</code></pre>'
        soup = _soup(html)
        h2md._collapse_code_spans(soup)
        code = soup.find("code")
        assert code is not None
        assert "echo hello" in code.get_text()

    def test_method_chaining_no_extra_spaces(self, h2md):
        html = (
            '<pre><code class="language-javascript">'
            '<span class="token class-name">Response</span>'
            '<span class="token punctuation">.</span>'
            '<span class="token function">json</span>'
            '<span class="token punctuation">(</span>'
            '<span class="token punctuation">)</span>'
            '</code></pre>'
        )
        soup = _soup(html)
        h2md._collapse_code_spans(soup)
        code = soup.find("code")
        assert code is not None
        text = code.get_text()
        assert "Response.json()" in text

    def test_full_shiki_fixture_converts_clean(self, h2md, read_fixture, workspace):
        html = read_fixture("shiki_code.html")
        (workspace / "raw.html").write_text(html)
        h2md._extract(workspace, selector=None)
        h2md._convert(workspace)
        md = (workspace / "article.raw.md").read_text()
        assert "```javascript" in md
        assert "express()" in md or "express();" in md
        assert "Response. json" not in md


class TestLanguageDetection:
    def test_data_language_attribute(self, h2md):
        html = '<pre data-language="rust"><code>fn main() {}</code></pre>'
        soup = _soup(html)
        pre = soup.find("pre")
        lang = h2md._code_language_callback(pre)
        assert lang == "rust"

    def test_data_lang_on_parent(self, h2md):
        html = '<div data-lang="go"><pre><code>func main() {}</code></pre></div>'
        soup = _soup(html)
        pre = soup.find("pre")
        lang = h2md._code_language_callback(pre)
        assert lang == "go"

    def test_sibling_tab_label_language(self, h2md):
        html = '<div><div class="CodeBlockTab">typescript</div><pre><code>const x: string = "hi";</code></pre></div>'
        soup = _soup(html)
        pre = soup.find("pre")
        lang = h2md._code_language_callback(pre)
        assert lang == "typescript"

    def test_sibling_filename_extension(self, h2md):
        html = '<div><span class="filename">app.rs</span><pre><code>fn main() {}</code></pre></div>'
        soup = _soup(html)
        pre = soup.find("pre")
        lang = h2md._code_language_callback(pre)
        assert lang == "rust"

    def test_sniff_sql(self, h2md):
        assert h2md._sniff_language("SELECT * FROM users WHERE id = 1") == "sql"
        assert h2md._sniff_language("CREATE TABLE users (id INT)") == "sql"

    def test_sniff_typescript(self, h2md):
        assert h2md._sniff_language("interface User {\n  name: string;\n}") == "typescript"
        assert h2md._sniff_language("type Foo = string | number") == "typescript"

    def test_class_prefix_still_wins(self, h2md):
        html = '<div data-language="go"><pre><code class="language-rust">fn main()</code></pre></div>'
        soup = _soup(html)
        pre = soup.find("pre")
        lang = h2md._code_language_callback(pre)
        assert lang == "rust"


class TestClassBasedTabFlattening:
    def test_flattens_codetabs_component(self, h2md, read_fixture):
        html = read_fixture("class_tabs.html")
        soup = _soup(html)
        h2md._preprocess_dom(soup)
        text = soup.get_text()
        headings = [h.get_text(strip=True) for h in soup.find_all("h4")]
        assert "curl" in headings
        assert "npm" in headings
        assert "brew" in headings
        assert "curl -fsSL" in text
        assert "npm install" in text
        assert "brew install" in text

    def test_skips_aria_tabs(self, h2md, read_fixture):
        html = read_fixture("tabbed_code.html")
        soup = _soup(html)
        h2md._flatten_class_tabs(soup)
        assert soup.find(attrs={"role": "tablist"}) is not None

    def test_tabs_with_nav_wrapper(self, h2md):
        html = """
        <div class="tabs">
            <nav><span>Python</span><span>Ruby</span></nav>
            <div class="tab-content"><pre><code>print("hi")</code></pre></div>
            <div class="tab-content"><pre><code>puts "hi"</code></pre></div>
        </div>
        """
        soup = _soup(html)
        h2md._flatten_class_tabs(soup)
        headings = [h.get_text(strip=True) for h in soup.find_all("h4")]
        assert "Python" in headings
        assert "Ruby" in headings

    def test_no_class_tabs_unchanged(self, h2md):
        html = "<div><pre><code>plain code</code></pre></div>"
        soup = _soup(html)
        h2md._flatten_class_tabs(soup)
        assert soup.find("h4") is None
        assert "plain code" in soup.get_text()


class TestCodeContainerCleanup:
    def test_removes_empty_chrome_siblings(self, h2md, read_fixture):
        from bs4 import Tag as BsTag

        html = read_fixture("code_with_chrome.html")
        soup = _soup(html)
        h2md._preprocess_dom(soup)
        figure = soup.find("figure")
        if figure and isinstance(figure, BsTag):
            children = [c for c in figure.children if isinstance(c, BsTag)]
            names = [c.name for c in children]
            assert "span" not in names or all(
                c.get_text(strip=True) for c in children if c.name == "span"
            )
        pre_tags = soup.find_all("pre")
        assert len(pre_tags) >= 2

    def test_preserves_code_content(self, h2md, read_fixture):
        html = read_fixture("code_with_chrome.html")
        soup = _soup(html)
        h2md._preprocess_dom(soup)
        text = soup.get_text()
        assert 'print("hello world")' in text
        assert "npm start" in text

    def test_copy_button_div_removed(self, h2md):
        from bs4 import Tag as BsTag

        html = """
        <figure class="code-block">
            <div class="copy-btn"></div>
            <pre><code>some code</code></pre>
        </figure>
        """
        soup = _soup(html)
        h2md._clean_code_containers(soup)
        figure = soup.find("figure")
        assert figure is not None and isinstance(figure, BsTag)
        divs = figure.find_all("div")
        assert len(divs) == 0

    def test_sibling_with_text_preserved(self, h2md):
        html = """
        <figure>
            <figcaption>Example output</figcaption>
            <pre><code>some output</code></pre>
        </figure>
        """
        soup = _soup(html)
        h2md._clean_code_containers(soup)
        assert "Example output" in soup.get_text()
