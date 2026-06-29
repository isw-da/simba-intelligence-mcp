"""Documentation tool implementations.

Wraps the bundled `docs/` directory, populated by `scripts/refresh-docs.sh`
from two upstream repos:

  isw-da/simba-intelligence-skill -> docs/skill/
    Setup guides, deployment walkthroughs, troubleshooting, install scripts.
    Exposed as: get_skill_overview, list_guides, read_guide,
                get_deployment_guide, search_docs, get_universal_llm_guide,
                get_install_script.

  isw-da/logi-si-docs -> docs/logi-si-docs/
    Full SI Mintlify corpus (llms-full.txt + per-page markdown),
    current Composer v25/v26 documentation, and the canonical Composer
    OpenAPI spec (220 paths, 338 operations). The Composer OpenAPI also
    covers the SI Discovery backend, which is byte-identical to the Composer
    backend (confirmed on simba.logisymphony.com 2026-06-26).
    Exposed as: search_si_mintlify, get_si_mintlify_corpus,
                search_composer_current_docs, get_composer_openapi_spec,
                search_composer_docs (legacy snippets, still present),
                get_composer_api_reference (legacy, still present).

RULE FOR ALL CALLERS: before answering any question about SI behaviour,
Composer API endpoints, configuration, or troubleshooting, call at minimum
one doc tool to ground the answer. Do not answer from training-data memory
alone.
"""

from __future__ import annotations

import re
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent
_DOCS_DIR = _PACKAGE_ROOT.parent.parent / "docs"
_SKILL_DIR = _DOCS_DIR / "skill"
_REFS_DIR = _SKILL_DIR / "references"
_SCRIPTS_DIR = _SKILL_DIR / "scripts"
_UNIVERSAL_DIR = _SKILL_DIR / "universal"
_COMPOSER_DIR = _DOCS_DIR / "composer"

# logi-si-docs mirror (populated by refresh-docs.sh)
_LOGI_SI_DIR = _DOCS_DIR / "logi-si-docs"
_SI_MINTLIFY_DIR = _LOGI_SI_DIR / "simba-intelligence"
_SI_MINTLIFY_PAGES_DIR = _SI_MINTLIFY_DIR / "pages"
_COMPOSER_CURRENT_DIR = _LOGI_SI_DIR / "logi-composer-current"
_COMPOSER_API_DIR = _LOGI_SI_DIR / "composer-api"

GUIDE_MAP: dict[str, str] = {
    "prerequisites": "prerequisites.md",
    "deployment-local": "deployment-local.md",
    "deployment-eks": "deployment-eks.md",
    "deployment-cloud": "deployment-cloud.md",
    "deployment-onprem": "deployment-onprem.md",
    "deployment-airgapped": "deployment-airgapped.md",
    "local-access": "local-access.md",
    "production-ingress": "production-ingress.md",
    "llm-config": "llm-config.md",
    "enabling-edcs": "enabling-edcs.md",
    "custom-edc-build": "custom-edc-build.md",
    "post-install": "post-install.md",
    "troubleshooting": "troubleshooting.md",
    "gui-install-guide": "gui-install-guide.md",
    "team-sharing": "team-sharing.md",
    "teardown": "teardown.md",
}

ENV_TO_GUIDE: dict[str, str] = {
    "local": "deployment-local",
    "docker-desktop": "deployment-local",
    "kind": "deployment-local",
    "eks": "deployment-eks",
    "aws": "deployment-eks",
    "aks": "deployment-cloud",
    "azure": "deployment-cloud",
    "gke": "deployment-cloud",
    "gcp": "deployment-cloud",
    "onprem": "deployment-onprem",
    "on-premises": "deployment-onprem",
    "on-prem": "deployment-onprem",
    "airgapped": "deployment-airgapped",
    "air-gapped": "deployment-airgapped",
}

SCRIPT_MAP: dict[tuple[str, str], str] = {
    ("local", "macos"): "install-si.sh",
    ("local", "linux"): "install-si.sh",
    ("local", "windows"): "install-si.ps1",
    ("aks", "macos"): "install-si-aks.sh",
    ("aks", "linux"): "install-si-aks.sh",
}


def _read(path: Path) -> str:
    if not path.exists():
        return f"(missing reference file: {path.name})"
    return path.read_text(encoding="utf-8")


def get_skill_overview() -> str:
    return _read(_SKILL_DIR / "SKILL.md")


def list_guides() -> list[str]:
    return list(GUIDE_MAP.keys())


def read_guide(name: str) -> str:
    if name not in GUIDE_MAP:
        return f"Guide '{name}' not found. Available: {', '.join(GUIDE_MAP.keys())}"
    return _read(_REFS_DIR / GUIDE_MAP[name])


def get_deployment_guide(environment: str) -> str:
    key = environment.lower().strip()
    guide = ENV_TO_GUIDE.get(key)
    if not guide:
        return (
            f"Unknown environment '{environment}'. "
            f"Supported: {', '.join(ENV_TO_GUIDE.keys())}. "
            "Run read_guide('prerequisites') first if this is a fresh machine."
        )
    return _read(_REFS_DIR / GUIDE_MAP[guide])


def search_docs(query: str) -> str:
    """Full-text search across all SI reference guides. Returns excerpts."""
    query_lower = query.lower()
    results: list[str] = []
    for name, filename in GUIDE_MAP.items():
        content = _read(_REFS_DIR / filename)
        lines = content.split("\n")
        excerpts: list[str] = []
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                excerpts.append("\n".join(lines[start:end]))
                if len(excerpts) >= 5:
                    break
        if excerpts:
            results.append(f"### {name}\n\n" + "\n\n---\n\n".join(excerpts))
    if not results:
        return f"No matches for '{query}' across SI documentation."
    return "\n\n".join(results)


def get_universal_llm_guide() -> str:
    return _read(_UNIVERSAL_DIR / "simba-intelligence-llm-guide.md")


def get_install_script(environment: str = "local", os_type: str = "macos") -> str:
    key = (environment.lower().strip(), os_type.lower().strip())
    script = SCRIPT_MAP.get(key)
    if not script:
        available = ", ".join(f"{e}/{o}" for (e, o) in SCRIPT_MAP)
        return (
            f"No pre-built script for {environment}/{os_type}. "
            f"Available combinations: {available}. "
            "For other environments, ask Claude to generate a custom script "
            "based on get_skill_overview() and the relevant deployment guide."
        )
    return _read(_SCRIPTS_DIR / script)


# --- Composer documentation -------------------------------------------------


def _list_composer_docs() -> list[Path]:
    if not _COMPOSER_DIR.exists():
        return []
    return sorted(_COMPOSER_DIR.rglob("*.md"))


def search_composer_docs(query: str) -> str:
    """Full-text search across the bundled Composer reference snippets."""
    query_lower = query.lower()
    results: list[str] = []
    for path in _list_composer_docs():
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        excerpts: list[str] = []
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                excerpts.append("\n".join(lines[start:end]))
                if len(excerpts) >= 5:
                    break
        if excerpts:
            name = path.relative_to(_COMPOSER_DIR).as_posix()
            results.append(f"### {name}\n\n" + "\n\n---\n\n".join(excerpts))
    if not results:
        return f"No matches for '{query}' across Composer documentation."
    return "\n\n".join(results)


def get_composer_api_reference(endpoint_path: str) -> str:
    """Return the bundled API reference entry for a Composer endpoint.

    Matches the longest entry whose declared path is a prefix of the
    requested path. Falls back to a textual search if no structured entry
    exists.
    """
    if not _COMPOSER_DIR.exists():
        return "(no Composer documentation bundled; check docs/composer/)"
    target = endpoint_path.strip().lstrip("/")
    api_ref = _COMPOSER_DIR / "api-reference.md"
    if api_ref.exists():
        text = api_ref.read_text(encoding="utf-8")
        # Sections are demarcated by ## /path/to/endpoint headings.
        sections = re.split(r"^## ", text, flags=re.MULTILINE)
        best: tuple[int, str] | None = None
        for section in sections[1:]:
            head, _, _ = section.partition("\n")
            head_path = head.strip().lstrip("/")
            if target.startswith(head_path) or head_path.startswith(target):
                score = len(head_path)
                if best is None or score > best[0]:
                    best = (score, "## " + section)
        if best:
            return best[1]
    # Fall back to full-text search.
    return search_composer_docs(endpoint_path)


# --- SI Mintlify corpus (isw-da/logi-si-docs) --------------------------------


def get_si_mintlify_corpus() -> str:
    """Return the full SI Mintlify documentation as a single text block.

    This is the llms-full.txt file from isw-da/logi-si-docs, which contains
    every SI product doc page concatenated into one LLM-friendly file. Use
    this when you need comprehensive coverage; use search_si_mintlify for
    targeted lookups.
    """
    corpus = _SI_MINTLIFY_DIR / "llms-full.txt"
    if not corpus.exists():
        return (
            "(SI Mintlify corpus not present. "
            "Run ./scripts/refresh-docs.sh to pull it from isw-da/logi-si-docs.)"
        )
    return corpus.read_text(encoding="utf-8")


def search_si_mintlify(query: str, max_results: int = 5) -> str:
    """Full-text search across the SI Mintlify docs (per-page markdown files).

    Searches the individual page files in docs/logi-si-docs/simba-intelligence/pages/
    and returns up to max_results excerpts. Prefer this over get_si_mintlify_corpus
    for targeted questions.
    """
    if not _SI_MINTLIFY_PAGES_DIR.exists():
        return (
            "(SI Mintlify pages not present. "
            "Run ./scripts/refresh-docs.sh to pull from isw-da/logi-si-docs.)"
        )
    query_lower = query.lower()
    results: list[str] = []
    for path in sorted(_SI_MINTLIFY_PAGES_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        excerpts: list[str] = []
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                excerpts.append("\n".join(lines[start:end]))
                if len(excerpts) >= 3:
                    break
        if excerpts:
            results.append(
                f"### {path.stem}\n\n" + "\n\n---\n\n".join(excerpts)
            )
        if len(results) >= max_results:
            break
    if not results:
        return f"No matches for '{query}' in SI Mintlify docs."
    return "\n\n".join(results)


# --- Current Composer docs (isw-da/logi-si-docs) ----------------------------


def search_composer_current_docs(query: str, version: str = "both", max_results: int = 5) -> str:
    """Full-text search across the current Composer v25/v26 documentation.

    version: 'v25', 'v26', or 'both' (default). Returns up to max_results
    excerpts. This covers the live product docs, unlike the legacy devnet
    articles which cover Composer v5/v6.
    """
    if not _COMPOSER_CURRENT_DIR.exists():
        return (
            "(Composer current docs not present. "
            "Run ./scripts/refresh-docs.sh to pull from isw-da/logi-si-docs.)"
        )
    query_lower = query.lower()
    results: list[str] = []
    versions = ["v25", "v26"] if version == "both" else [version]
    for ver in versions:
        ver_dir = _COMPOSER_CURRENT_DIR / ver
        if not ver_dir.exists():
            continue
        for path in sorted(ver_dir.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            lines = content.split("\n")
            excerpts: list[str] = []
            for i, line in enumerate(lines):
                if query_lower in line.lower():
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    excerpts.append("\n".join(lines[start:end]))
                    if len(excerpts) >= 3:
                        break
            if excerpts:
                results.append(
                    f"### [{ver}] {path.stem}\n\n" + "\n\n---\n\n".join(excerpts)
                )
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break
    if not results:
        return f"No matches for '{query}' in Composer {version} docs."
    return "\n\n".join(results)


# --- Composer OpenAPI spec (isw-da/logi-si-docs) -----------------------------


def get_composer_openapi_spec(path_filter: str = "") -> str:
    """Return the canonical Composer OpenAPI spec (220 paths, 338 ops).

    This spec also covers the SI Discovery backend (/discovery/api/*), which
    is byte-identical to the Composer backend. Pulled from the live
    simba.logisymphony.com instance and stored in
    docs/logi-si-docs/composer-api/composer-openapi.json.

    If path_filter is provided, only paths containing that string are returned.
    Leave it empty to get the full spec (large — prefer path_filter or
    ENDPOINTS.md for targeted lookups).
    """
    spec_file = _COMPOSER_API_DIR / "composer-openapi.json"
    if not spec_file.exists():
        return (
            "(Composer OpenAPI spec not present. "
            "Run ./scripts/refresh-docs.sh to pull from isw-da/logi-si-docs.)"
        )
    if not path_filter:
        endpoints_md = _COMPOSER_API_DIR / "ENDPOINTS.md"
        if endpoints_md.exists():
            return (
                "Full spec is large. Returning ENDPOINTS.md index instead. "
                "Pass a path_filter to get specific endpoint detail.\n\n"
                + endpoints_md.read_text(encoding="utf-8")
            )
        return spec_file.read_text(encoding="utf-8")

    import json
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    paths = spec.get("paths", {})
    matched = {p: v for p, v in paths.items() if path_filter.lower() in p.lower()}
    if not matched:
        return f"No paths matching '{path_filter}' in the Composer OpenAPI spec."
    return json.dumps({"openapi": spec.get("openapi"), "paths": matched}, indent=2)
