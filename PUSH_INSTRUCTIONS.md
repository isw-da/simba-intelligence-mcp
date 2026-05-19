# Push instructions

The sandbox running Claude Code blocked `git init`, `git add`, `git commit`,
and `git push` on the previous attempt. `gh repo create` did work. If the
sandbox is still in the way when you read this, run the commands below
from your terminal. They assume `gh` is authenticated against `isw-da` and
that `github.com/isw-da/simba-intelligence-mcp` already exists (empty).

## Steps

```bash
cd ~/claude-ai-projects/simba-intelligence/simba-intelligence-mcp

git init
git checkout -b main
git add .
git commit -m "Initial commit: SI MCP with 52 tools (SI surface plus Composer admin / embed / docs)"
git remote add origin git@github.com:isw-da/simba-intelligence-mcp.git
git push -u origin main
```

If `gh` is your auth path, swap the remote URL for `https://github.com/isw-da/simba-intelligence-mcp.git`.

## After the push

1. Re-run `./scripts/refresh-docs.sh` on the cloned copy to bring the SI
   skill content into `docs/skill/` (the skill content is not committed;
   the script syncs it on demand). The Composer reference snippets in
   `docs/composer/` are committed and need no refresh.
2. Verify the smoke tests pass:
   ```bash
   uv run pytest tests/
   ```

## Why the sandbox blocked git

Claude Code runs commands inside a sandbox that denies network and certain
filesystem-mutating tools, including `git init` and `git push`. Nothing
about the repo itself is unusual; running the commands above from your
normal shell should succeed.
