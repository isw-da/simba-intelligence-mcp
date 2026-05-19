# simba-intelligence-mcp

MCP server exposing the full Simba Intelligence (SI) surface as tools for
Claude Desktop, Claude Code, and any other MCP client. Once configured,
Claude can introspect a local or hosted SI deployment, run chat queries,
manage connections and sources, manage users, run raw SQL, mint Composer
embed tokens, and read every SI and Composer reference guide without
manual file uploads.

SI is built on top of Logi Composer. The SI Helm chart aliases the Composer
subchart as `discovery`, EDC connectors live in Composer, and the SI
reference guides routinely point at Composer admin patterns. This MCP
therefore carries both surfaces in one place, with the Composer slice
scoped to what SI operators and SE teams actually reach for (admin reads,
embed tokens, branding, generic API escape hatch, and bundled doc lookup).

For dashboard authoring at scale (widget layout, field links, time scope,
bulk import), use the dedicated
[`isw-da/composer-mcp`](https://github.com/isw-da/composer-mcp) server as a
complement.

Companion to the documentation-only
[`isw-da/simba-intelligence-skill`](https://github.com/isw-da/simba-intelligence-skill).

## Tools

Fifty-two tools across ten groups.

Documentation, SI (seven, skill content only, no SI required):

| Tool | Description |
| --- | --- |
| `get_skill_overview` | Full SKILL.md (architecture, decision trees, troubleshooting quick reference) |
| `list_guides` | Names of every reference guide |
| `read_guide(name)` | Read one guide by name |
| `get_deployment_guide(environment)` | Deployment guide for local / eks / aks / gke / onprem / airgapped |
| `search_docs(query)` | Full-text search across every reference guide |
| `get_universal_llm_guide` | Consolidated guide for non-Claude LLM clients |
| `get_install_script(environment, os_type)` | Bundled install script content |

Documentation, Composer (two):

| Tool | Description |
| --- | --- |
| `search_composer_docs(query)` | Full-text search across the bundled Composer reference snippets |
| `get_composer_api_reference(endpoint_path)` | Return the bundled reference entry for a Composer endpoint |

Authentication (one):

| Tool | Description |
| --- | --- |
| `authenticate(base_url, username, password)` | Exchange credentials for a bearer cached on the MCP session |

SI introspection (eight):

| Tool | Description |
| --- | --- |
| `si_api_call(method, path, body, params)` | Generic SI request escape hatch |
| `si_health` | `GET /api/v1/healthz` |
| `si_version` | Return the SI build version |
| `si_user` | Current authenticated user |
| `si_llm_config` | Active BYOLLM configuration |
| `si_list_connectors` | Installed EDC and Discovery connectors |
| `si_list_tenants` | Tenants visible to the caller |
| `si_list_permissions` | Permissions defined in the active tenant |

SI chat (two):

| Tool | Description |
| --- | --- |
| `si_chat_query(question, source_id)` | Natural language question, streamed answer |
| `si_chat_history(limit)` | Caller's recent chat history |

SI connections (six):

| Tool | Description |
| --- | --- |
| `si_list_connections`, `si_get_connection`, `si_create_connection`, `si_update_connection`, `si_delete_connection`, `si_test_connection` | Connection CRUD plus payload validation |

SI sources (six):

| Tool | Description |
| --- | --- |
| `si_list_sources`, `si_get_source`, `si_create_source`, `si_update_source`, `si_delete_source`, `si_run_schema_discovery` | Source CRUD plus schema discovery |

SI identity (eight):

| Tool | Description |
| --- | --- |
| `si_list_users`, `si_get_user`, `si_create_user`, `si_list_groups`, `si_get_group`, `si_create_group`, `si_get_tenant`, `si_create_tenant` | Users, groups, and tenants |

SI query (two):

| Tool | Description |
| --- | --- |
| `si_execute_query(source_id, sql, limit)` | Run raw SQL against a source |
| `si_explain_query(source_id, sql)` | Return the engine plan without executing |

Composer admin and embed (ten):

| Tool | Description |
| --- | --- |
| `composer_list_dashboards` | List every Composer dashboard |
| `composer_get_dashboard(dashboard_id)` | Read one Composer dashboard document |
| `composer_list_visuals` | List every Composer visual |
| `composer_get_visual(visual_id)` | Read one Composer visual document |
| `composer_list_themes` | List every Composer theme |
| `composer_get_theme(theme_id)` | Read one Composer theme document |
| `composer_get_branding` | Active branding configuration (logo, palette, fonts) |
| `composer_list_scheduled_reports` | List every Composer scheduled report |
| `composer_create_embed_token(payload)` | Mint a trusted-access pull or push embed token |
| `composer_api_call(method, suffix, body, params)` | Generic Composer API escape hatch |

## Prerequisites

- Python 3.10 or newer
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or any other Python package manager
- A running SI deployment, either local (kind cluster, port-forwarded per the setup skill) or hosted (e.g. `https://simba.logisymphony.com/`)
- An SI API key, or a username and password the MCP can exchange for a bearer

The documentation tools work without an SI connection. The API tools need at least `SI_BASE_URL` and one of `SI_API_KEY` or `SI_USERNAME` + `SI_PASSWORD`.

## Install

```bash
git clone https://github.com/isw-da/simba-intelligence-mcp.git
cd simba-intelligence-mcp
./scripts/refresh-docs.sh   # pulls a fresh copy of the SI setup skill into docs/skill/
uv sync
```

Or with `pip`:

```bash
pip install -e .
./scripts/refresh-docs.sh
```

The `refresh-docs.sh` step pulls the SI setup skill (`isw-da/simba-intelligence-skill`) into `docs/skill/` so the documentation tools (`get_skill_overview`, `list_guides`, etc.) have content to serve. Re-run it whenever the upstream skill changes. The Composer reference snippets in `docs/composer/` ship with the repo and do not need a refresh step.

## Configure environment

Copy `.env.example` to `.env` (or export the variables in your shell):

```bash
export SI_BASE_URL="http://localhost:8080"
export SI_API_KEY="<your local SI API key>"
# Composer context: /discovery when bundled in SI, /composer when standalone.
export SI_COMPOSER_CONTEXT="/discovery"
# Or, for username and password fallback:
# export SI_USERNAME="amin.hasan@insightsoftware.com"
# export SI_PASSWORD="<password>"
```

For a local kind deployment, make sure the port-forwards from the setup skill are running:

```bash
kubectl -n simba-intel port-forward svc/si-simba-intelligence-chart 8082:5050
kubectl -n simba-intel port-forward svc/si-discovery-web 8081:9050
docker run --rm -p 8080:8080 -v /tmp/Caddyfile:/etc/caddy/Caddyfile caddy:2
```

## Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "simba-intelligence": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/simba-intelligence-mcp",
        "run",
        "simba-intelligence-mcp"
      ],
      "env": {
        "SI_BASE_URL": "http://localhost:8080",
        "SI_API_KEY": "<your local SI API key>",
        "SI_COMPOSER_CONTEXT": "/discovery"
      }
    }
  }
}
```

Restart Claude Desktop. Open a new chat and run a quick sanity check:

> List the available SI setup guides.

Claude should call `list_guides` and return the full set.

## Add to Claude Code

```bash
claude mcp add simba-intelligence \
  --command uv \
  --arg --directory --arg /path/to/simba-intelligence-mcp \
  --arg run --arg simba-intelligence-mcp \
  --env SI_BASE_URL=http://localhost:8080 \
  --env SI_API_KEY=<your local SI API key> \
  --env SI_COMPOSER_CONTEXT=/discovery
```

## Auth flow when no API key is set

```text
authenticate(base_url="http://localhost:8080",
             username="amin.hasan@insightsoftware.com",
             password="...")
```

The returned bearer is cached on the running MCP process for every subsequent tool call. There is no persistence: restarting the MCP requires re-authenticating.

## Targeting a different SI instance

Either set `SI_BASE_URL` before launching the MCP, or pass `base_url` to `authenticate` to redirect a running session. Do not hard-code production hosts in the repo.

## Relationship to `composer-mcp`

`isw-da/composer-mcp` is the dashboard-authoring server, aimed at Composer developers building visuals, layouts, field links, and time scope at scale. The two servers coexist for different audiences:

- Reach for `simba-intelligence-mcp` when the entry point is SI: setup, port-forwards, BYOLLM, EDCs, NLQ, identity, and the Composer admin reads or embed tokens you need alongside an SI deployment.
- Reach for `composer-mcp` when the entry point is Composer itself and the work is dashboard authoring.

There is intentional overlap in the Composer admin surface; the SI MCP would be artificially crippled without it.

## Repository layout

```text
simba-intelligence-mcp/
  pyproject.toml
  README.md
  .env.example
  src/simba_intelligence_mcp/
    __init__.py
    server.py           FastMCP entry point and tool registrations
    client.py           HTTP client (httpx) with bearer + SSE support
    docs.py             Documentation tool implementations (SI + Composer)
    tools/
      __init__.py
      si_admin.py       Generic SI helpers + introspection
      si_chat.py        Chat / NLQ
      si_connections.py Connection CRUD
      si_sources.py     Source CRUD + schema discovery
      si_users.py       Users, groups, tenants
      si_query.py       Raw SQL execution + explain
      composer_admin.py Composer admin reads, embed tokens, generic call
  docs/
    skill/              Mirror of isw-da/simba-intelligence-skill content
    composer/           Composer v25 REST reference snippets
  tests/                Smoke tests (see `tests/README.md`)
```

## Licence

Copyright insightsoftware. Internal use.
