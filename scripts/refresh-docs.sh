#!/usr/bin/env bash
# Sync documentation into docs/ from two upstream repos.
#
# Sources pulled on every run:
#   1. isw-da/simba-intelligence-skill  -> docs/skill/
#      Setup guides, deployment walkthroughs, troubleshooting, install scripts.
#
#   2. isw-da/logi-si-docs              -> docs/logi-si-docs/
#      Full SI Mintlify corpus (llms-full.txt + per-page markdown),
#      current Composer v25/v26 documentation, and the canonical Composer
#      OpenAPI spec (220 paths / 338 operations).
#      The full devnet archive (15k+ articles) is NOT pulled here; it is
#      available directly from the logi-si-docs repo for offline reference.
#
# Usage:
#   ./scripts/refresh-docs.sh
#     -- pulls both repos from GitHub
#
#   ./scripts/refresh-docs.sh /path/to/skill-clone /path/to/logi-si-docs-clone
#     -- copies from local clones (fast, useful during development)
#
# Re-run whenever either upstream changes.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_DEST="$ROOT/docs/skill"
LOGI_DEST="$ROOT/docs/logi-si-docs"

sync_skill() {
    local src="$1"
    echo "Syncing skill content from: $src"
    rm -rf "$SKILL_DEST"
    cp -R "$src/simba-intelligence-setup" "$SKILL_DEST"
    echo "  docs/skill/ done ($(ls "$SKILL_DEST" | wc -l | tr -d ' ') items)"
}

sync_logi_si_docs() {
    local src="$1"
    echo "Syncing logi-si-docs from: $src"
    rm -rf "$LOGI_DEST"
    mkdir -p "$LOGI_DEST"
    # SI Mintlify corpus
    cp -R "$src/simba-intelligence" "$LOGI_DEST/simba-intelligence"
    # Current Composer docs (v25 + v26 — legacy devnet v5/v6 is intentionally excluded)
    cp -R "$src/logi-composer-current" "$LOGI_DEST/logi-composer-current"
    # Composer OpenAPI + endpoint index
    cp -R "$src/composer-api" "$LOGI_DEST/composer-api"
    echo "  docs/logi-si-docs/ done"
    echo "    SI Mintlify: $(ls "$LOGI_DEST/simba-intelligence/pages" 2>/dev/null | wc -l | tr -d ' ') pages"
    echo "    Composer v25: $(ls "$LOGI_DEST/logi-composer-current/v25" 2>/dev/null | wc -l | tr -d ' ') articles"
    echo "    Composer v26: $(ls "$LOGI_DEST/logi-composer-current/v26" 2>/dev/null | wc -l | tr -d ' ') articles"
    echo "    OpenAPI paths: $(python3 -c "import json,sys; d=json.load(open('$LOGI_DEST/composer-api/composer-openapi.json')); print(len(d.get('paths',{})))" 2>/dev/null || echo '?')"
}

if [ $# -ge 2 ]; then
    sync_skill "$1"
    sync_logi_si_docs "$2"
elif [ $# -eq 1 ]; then
    echo "error: pass either zero or two arguments (skill-path logi-si-docs-path)" >&2
    exit 1
else
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT

    echo "Cloning isw-da/simba-intelligence-skill ..."
    git clone --depth 1 https://github.com/isw-da/simba-intelligence-skill.git "$TMP/skill"
    sync_skill "$TMP/skill"

    echo "Cloning isw-da/logi-si-docs ..."
    git clone --depth 1 https://github.com/isw-da/logi-si-docs.git "$TMP/logi-si-docs"
    sync_logi_si_docs "$TMP/logi-si-docs"
fi

echo ""
echo "refresh-docs complete. Re-run whenever either upstream changes."
