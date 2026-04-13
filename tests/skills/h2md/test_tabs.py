from __future__ import annotations


def test_aria_tablist_flattened(pipeline, read_fixture):
    r = pipeline(read_fixture("tabbed_code.html"))
    assert "curl -fsSL" in r.md
    assert "npm install" in r.md
    assert "brew install" in r.md


def test_class_based_tabs_flattened(pipeline, read_fixture):
    r = pipeline(read_fixture("class_tabs.html"))
    assert "curl -fsSL" in r.md
    assert "npm install" in r.md
    assert "brew install" in r.md


def test_terminal_regions_reconstructed(pipeline, read_fixture):
    r = pipeline(read_fixture("terminal_output.html"))
    assert "Bun" in r.md
    assert "v1.3.12" in r.md


def test_nav_wrapper_tabs_flattened(pipeline):
    html = """<!DOCTYPE html><html><body><article>
    <h1>Install</h1>
    <p>Pick a language:</p>
    <div class="tabs">
        <nav><span>Python</span><span>Ruby</span></nav>
        <div class="tab-content"><pre><code>print("hi")</code></pre></div>
        <div class="tab-content"><pre><code>puts "hi"</code></pre></div>
    </div>
    </article></body></html>"""
    r = pipeline(html)
    assert 'print("hi")' in r.md
    assert 'puts "hi"' in r.md
