#!/usr/bin/env bash
# Sync the SI setup skill content into docs/skill/.
#
# The MCP's documentation tools (get_skill_overview, list_guides, read_guide,
# get_deployment_guide, search_docs, get_universal_llm_guide, get_install_script)
# load from docs/skill/. We deliberately don't vendor the content into git
# to avoid two sources of truth; this script pulls a fresh copy on demand.
#
# Usage:
#   ./scripts/refresh-docs.sh                       # clone from isw-da/simba-intelligence-skill
#   ./scripts/refresh-docs.sh /path/to/local/skill  # copy from a local clone
#
# Run after the initial clone, and again whenever the upstream skill changes.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/docs/skill"

if [ $# -ge 1 ]; then
    SRC="$1/simba-intelligence-setup"
    if [ ! -d "$SRC" ]; then
        echo "error: $SRC not found. Pass the path to your local simba-intelligence-skill clone." >&2
        exit 1
    fi
    echo "Syncing from local path: $SRC"
    rm -rf "$DEST"
    cp -R "$SRC" "$DEST"
else
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    echo "Cloning isw-da/simba-intelligence-skill into $TMP"
    git clone --depth 1 https://github.com/isw-da/simba-intelligence-skill.git "$TMP"
    rm -rf "$DEST"
    cp -R "$TMP/simba-intelligence-setup" "$DEST"
fi

echo "Done. docs/skill/ now mirrors isw-da/simba-intelligence-skill."
ls "$DEST" | head -10
