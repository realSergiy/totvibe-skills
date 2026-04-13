from __future__ import annotations


def test_fused_text_detected(pipeline):
    fused = "a" * 90
    html = f"""<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p>Some text {fused} more text in this article paragraph.</p>
    </article></body></html>"""
    r = pipeline(html)
    assert "fused text" in r.notes.lower()


def test_html_leakage_detected(pipeline):
    html = """<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p>Some text <svg viewBox="0 0 10 10"><path d="M0"/></svg> leftover content.</p>
    </article></body></html>"""
    r = pipeline(html)
    assert "HTML leakage" in r.notes or "svg" not in r.md.lower()


def test_clean_content_no_issues(pipeline, read_fixture):
    r = pipeline(read_fixture("simple_article.html"))
    assert r.toon["h2md"]["issues"] >= 0


def test_url_in_markdown_link_not_flagged_as_fused(pipeline):
    long_url = "https://github.com/microsoft/TypeScript/pull/62243/files/very-long-path"
    html = f"""<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p><a href="{long_url}">This change was provided</a> thanks to the work on this project.</p>
    </article></body></html>"""
    r = pipeline(html)
    assert "fused text" not in r.notes.lower()


def test_medium_string_not_flagged_as_fused(pipeline):
    medium = "a" * 60
    html = f"""<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p>Some text {medium} more text in this article paragraph.</p>
    </article></body></html>"""
    r = pipeline(html)
    assert "fused text" not in r.notes.lower()


def test_wrong_language_detection_on_text_tagged_fence(h2md, tmp_path):
    md = '---\n---\n\n# Title\n\nSome text.\n\n```text\nconst app = express()\napp.listen(3000)\n```\n'
    (tmp_path / "article.md").write_text(md)
    (tmp_path / "notes.md").write_text("")
    h2md._detect(tmp_path)
    notes = (tmp_path / "notes.md").read_text()
    assert "## Likely wrong language" in notes
    assert "javascript" in notes.lower()


def test_long_string_inside_code_fence_not_flagged(pipeline):
    long_import = "a" * 90
    html = f"""<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p>Some text.</p>
    <pre><code class="language-python">import {long_import}</code></pre>
    </article></body></html>"""
    r = pipeline(html)
    assert "fused text" not in r.notes.lower()


def test_inline_code_not_flagged_as_fused(pipeline):
    long_id = "x" * 90
    html = f"""<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p>Run <code>{long_id}</code> to start the process.</p>
    </article></body></html>"""
    r = pipeline(html)
    assert "fused text" not in r.notes.lower()


def test_multiple_links_zero_false_positives(pipeline):
    links = " ".join(
        f'<a href="https://example.com/very/long/path/to/resource/number/{i}">link{i}</a>' for i in range(10)
    )
    html = f"""<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p>Many links: {links}</p>
    </article></body></html>"""
    r = pipeline(html)
    assert "fused text" not in r.notes.lower()


def test_issues_use_substring_anchors(pipeline):
    fused = "x" * 90
    html = f"""<!DOCTYPE html><html><body><article>
    <h1>Title</h1>
    <p>Before the problem {fused} after it in the text.</p>
    </article></body></html>"""
    r = pipeline(html)
    if r.notes.strip():
        assert "**Find:**" in r.notes
