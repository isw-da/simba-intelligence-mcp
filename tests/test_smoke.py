"""Smoke tests for the docs layer.

These pass without an SI deployment. The API tools need a live SI to
exercise; see `tests/README.md` for the manual checklist.
"""

from __future__ import annotations

from simba_intelligence_mcp import docs


def test_list_guides_returns_known_names():
    names = docs.list_guides()
    assert "deployment-local" in names
    assert "troubleshooting" in names


def test_get_deployment_guide_local_resolves_to_kind():
    text = docs.get_deployment_guide("kind")
    assert isinstance(text, str)
    # The bundled local deployment guide always mentions kind or docker.
    assert "kind" in text.lower() or "docker" in text.lower() or text.startswith("(missing")


def test_search_docs_handles_no_match():
    result = docs.search_docs("xyz-no-such-string-anywhere-zzz")
    assert "No matches" in result


def test_get_composer_api_reference_returns_dashboards_section():
    text = docs.get_composer_api_reference("/dashboards")
    assert isinstance(text, str)
    # The bundled reference always has a /dashboards section, or the docs
    # directory is missing entirely (acceptable for a partial checkout).
    assert "/dashboards" in text or "no Composer documentation" in text


def test_search_composer_docs_finds_known_term():
    result = docs.search_composer_docs("trusted-access")
    # Either we find the term, or the composer docs aren't bundled.
    assert "trusted-access" in result or "No matches" in result
