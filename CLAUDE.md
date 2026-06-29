# simba-intelligence-mcp — coding rules

## Documentation is mandatory, not optional

**Before answering any question about SI behaviour, Composer API endpoints,
configuration, or troubleshooting, call at least one doc tool.**

Do not answer from training-data memory. The tools exist precisely because
SI and Composer move fast and the model's training cut-off is behind the
product. A confident wrong answer based on stale training data is worse than
a slightly slower answer grounded in the bundled docs.

Preferred lookup order:

1. `search_si_mintlify(query)` — product behaviour, NLQ, LLM config, EDCs, RLS
2. `search_composer_current_docs(query)` — Composer v25/v26 REST API patterns,
   dashboard authoring, embed tokens, data models
3. `get_composer_openapi_spec(path_filter)` — exact endpoint shape, params,
   request/response schemas
4. `search_docs(query)` — setup, deployment, troubleshooting (skill guides)
5. `read_guide(name)` — full text of a specific setup guide

The docs corpus is in `docs/logi-si-docs/` (SI Mintlify + Composer current +
OpenAPI) and `docs/skill/` (setup guides). Both are populated by
`./scripts/refresh-docs.sh`. Re-run it after pulling either upstream repo.

## SI / Composer architecture facts

- SI is built on Logi Composer. The SI Helm chart aliases the Composer
  subchart as `discovery`. EDC connectors live in Composer.
- The SI Discovery backend (`/discovery/api/*`) is byte-identical to the
  Composer backend (`/composer/api/*`). There is one OpenAPI spec for both.
- SI's own NLQ chat endpoints (`/api/v1/*`) use session/SSO auth and publish
  no OpenAPI. The only machine-readable API spec is the Composer/Discovery
  one captured in `docs/logi-si-docs/composer-api/composer-openapi.json`.
- Composer APIs are available to SI callers via the `/discovery` context.
  The env var `SI_COMPOSER_CONTEXT` controls the prefix (default `/discovery`
  for bundled SI, `/composer` for standalone).

## Upstream doc repos

- `isw-da/simba-intelligence-skill` — setup skill, refresh into `docs/skill/`
- `isw-da/logi-si-docs` — full doc corpus, refresh into `docs/logi-si-docs/`

Both are public. Re-run `./scripts/refresh-docs.sh` to pull the latest.

## Coding rules

- British English in prose, comments, and commit messages.
- Touch only what the task requires.
- No new abstractions unless the task demands it.
- Read `docs.py` before adding or changing a doc tool. Read `server.py` before
  registering a new tool.
