from __future__ import annotations


def test_sniff_language_toml(h2md):
    assert h2md._sniff_language("[package]\nname = 'foo'") == "toml"


def test_sniff_language_bash(h2md):
    assert h2md._sniff_language("curl -fsSL https://example.com") == "bash"
    assert h2md._sniff_language("npm install express") == "bash"


def test_sniff_language_json(h2md):
    assert h2md._sniff_language('{"key": "value"}') == "json"


def test_sniff_language_python(h2md):
    assert h2md._sniff_language("from fastapi import FastAPI\n\napp = FastAPI()") == "python"


def test_sniff_language_javascript(h2md):
    assert h2md._sniff_language("const app = () => {}") == "javascript"


def test_sniff_language_tsx(h2md):
    assert h2md._sniff_language("<Button onClick={handler}>Click</Button>") == "tsx"


def test_sniff_language_default_text(h2md):
    assert h2md._sniff_language("some plain text output") == "text"
    assert h2md._sniff_language("") == "text"


def test_convert_preserves_code_language_from_class(h2md, workspace):
    html = '<pre><code class="language-python">print("hi")</code></pre>'
    (workspace / "article.html").write_text(html)
    manifest = h2md.Manifest(url="https://example.com")
    h2md._convert(workspace, manifest, force=True)
    md = (workspace / "article.raw.md").read_text()
    assert "```python" in md
    assert 'print("hi")' in md


def test_convert_sniffs_language_when_no_class(h2md, workspace):
    html = '<pre><code>curl -fsSL https://example.com/install.sh | bash</code></pre>'
    (workspace / "article.html").write_text(html)
    manifest = h2md.Manifest(url="https://example.com")
    h2md._convert(workspace, manifest, force=True)
    md = (workspace / "article.raw.md").read_text()
    assert "```bash" in md


def test_convert_headings_preserved(h2md, workspace):
    html = "<h1>Title</h1><h2>Section</h2><p>Content</p>"
    (workspace / "article.html").write_text(html)
    manifest = h2md.Manifest(url="https://example.com")
    h2md._convert(workspace, manifest, force=True)
    md = (workspace / "article.raw.md").read_text()
    assert "# Title" in md
    assert "## Section" in md


def test_convert_links_preserved(h2md, workspace):
    html = '<p>Visit <a href="https://example.com">our site</a> for more.</p>'
    (workspace / "article.html").write_text(html)
    manifest = h2md.Manifest(url="https://example.com")
    h2md._convert(workspace, manifest, force=True)
    md = (workspace / "article.raw.md").read_text()
    assert "[our site](https://example.com)" in md
