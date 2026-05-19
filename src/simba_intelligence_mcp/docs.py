"""Documentation tool implementations.

Wraps the bundled `docs/` directory which carries:

  - A copy of the SKILL.md overview from `isw-da/simba-intelligence-skill`
  - The reference guides (deployment-*, llm-config, troubleshooting, etc.)
  - The universal LLM guide for non-Claude clients
  - Install scripts (macOS, Linux, Windows, AKS)

The MCP exposes these as `get_skill_overview`, `list_guides`, `read_guide`,
`get_deployment_guide`, `search_docs`, `get_universal_llm_guide`, and
`get_install_script`.
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
