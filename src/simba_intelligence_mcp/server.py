"""FastMCP entry point for simba-intelligence-mcp.

Registers documentation tools (skill content), SI Discovery API tools,
and an authentication helper. Run via the `simba-intelligence-mcp`
console script or `python -m simba_intelligence_mcp.server`.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import docs as docs_mod
from .client import SIClient, SIConfig
from .tools import (
    composer_admin,
    si_admin,
    si_chat,
    si_connections,
    si_query,
    si_sources,
    si_users,
)

mcp = FastMCP("simba-intelligence-mcp")

# Single client per MCP process. We lazy-init so the server can start even
# when no SI is reachable (the documentation tools still work).
_client: SIClient | None = None


def _get_client() -> SIClient:
    global _client
    if _client is None:
        _client = SIClient(SIConfig())
    return _client


def _fmt(value: Any) -> str:
    return si_admin.si_pretty(value)


# --- Documentation tools ----------------------------------------------------


@mcp.tool()
def get_skill_overview() -> str:
    """Return the full SI setup SKILL.md (architecture, decision trees, troubleshooting)."""
    return docs_mod.get_skill_overview()


@mcp.tool()
def list_guides() -> list[str]:
    """List every reference guide name. Pass any one to `read_guide`."""
    return docs_mod.list_guides()


@mcp.tool()
def read_guide(name: str) -> str:
    """Read a specific reference guide by name (e.g. 'deployment-local', 'troubleshooting')."""
    return docs_mod.read_guide(name)


@mcp.tool()
def get_deployment_guide(environment: str) -> str:
    """Return the deployment guide for one of: local, eks, aks, gke, onprem, airgapped."""
    return docs_mod.get_deployment_guide(environment)


@mcp.tool()
def search_docs(query: str) -> str:
    """Full-text search across every SI reference guide. Returns excerpts grouped by guide."""
    return docs_mod.search_docs(query)


@mcp.tool()
def get_universal_llm_guide() -> str:
    """Return the consolidated SI guide for non-Claude LLM clients."""
    return docs_mod.get_universal_llm_guide()


@mcp.tool()
def get_install_script(environment: str = "local", os_type: str = "macos") -> str:
    """Return the bundled install script for the given environment and OS."""
    return docs_mod.get_install_script(environment, os_type)


# --- Authentication ---------------------------------------------------------


@mcp.tool()
def authenticate(base_url: str = "", username: str = "", password: str = "") -> str:
    """Exchange username and password for a bearer token, cached for the session.

    Pass an explicit `base_url` to redirect the MCP at a different SI instance
    (e.g. `https://<si-host>`). If username and password are
    omitted, the values from `SI_USERNAME` and `SI_PASSWORD` are used.
    """
    client = _get_client()
    user = username or os.environ.get("SI_USERNAME", "")
    pwd = password or os.environ.get("SI_PASSWORD", "")
    if not user or not pwd:
        return "Set SI_USERNAME and SI_PASSWORD (or pass them as arguments) before calling authenticate()."
    try:
        token = client.authenticate(base_url or None, user, pwd)
        return f"Authenticated. Bearer cached for this MCP session (length {len(token)})."
    except Exception as e:
        return f"Authentication failed: {e}"


# --- SI generic helpers -----------------------------------------------------


@mcp.tool()
def si_api_call(method: str, path: str, body: dict | list | None = None, params: dict | None = None) -> str:
    """Make an arbitrary SI Discovery / main app request.

    Pass the full path with namespace, e.g. `/discovery/api/sources` or
    `/api/v1/healthz`. Use this for any endpoint not covered by a dedicated tool.
    """
    return _fmt(si_admin.si_api_call(_get_client(), method, path, body, params))


@mcp.tool()
def si_health() -> str:
    """Hit `GET /api/v1/healthz`."""
    return _fmt(si_admin.si_health(_get_client()))


@mcp.tool()
def si_version() -> str:
    """Return the SI build version."""
    return _fmt(si_admin.si_version(_get_client()))


@mcp.tool()
def si_user() -> str:
    """Return the currently authenticated SI user."""
    return _fmt(si_admin.si_user(_get_client()))


@mcp.tool()
def si_llm_config() -> str:
    """Return the active LLM configuration (provider, model, key reference)."""
    return _fmt(si_admin.si_llm_config(_get_client()))


@mcp.tool()
def si_list_connectors() -> str:
    """List installed Discovery / EDC connectors."""
    return _fmt(si_admin.si_list_connectors(_get_client()))


@mcp.tool()
def si_list_tenants() -> str:
    """List tenants visible to the caller."""
    return _fmt(si_admin.si_list_tenants(_get_client()))


@mcp.tool()
def si_list_permissions() -> str:
    """List permissions defined in the active tenant."""
    return _fmt(si_admin.si_list_permissions(_get_client()))


# --- SI chat ----------------------------------------------------------------


@mcp.tool()
def si_chat_query(question: str, source_id: str = "") -> str:
    """Ask SI a natural language question. Returns the stitched chat answer."""
    return si_chat.si_chat(_get_client(), question, source_id or None)


@mcp.tool()
def si_chat_history(limit: int = 20) -> str:
    """Return the caller's recent chat history (default 20 entries)."""
    return _fmt(si_chat.si_chat_history(_get_client(), limit))


# --- SI connections ---------------------------------------------------------


@mcp.tool()
def si_list_connections() -> str:
    """List every Discovery connection."""
    return _fmt(si_connections.list_connections(_get_client()))


@mcp.tool()
def si_get_connection(connection_id: str) -> str:
    """Read one Discovery connection."""
    return _fmt(si_connections.get_connection(_get_client(), connection_id))


@mcp.tool()
def si_create_connection(payload: dict) -> str:
    """Create a Discovery connection. Payload shape depends on the connector type."""
    return _fmt(si_connections.create_connection(_get_client(), payload))


@mcp.tool()
def si_update_connection(connection_id: str, payload: dict) -> str:
    """Update a Discovery connection. Send the full document, not a patch."""
    return _fmt(si_connections.update_connection(_get_client(), connection_id, payload))


@mcp.tool()
def si_delete_connection(connection_id: str) -> str:
    """Delete a Discovery connection. Fails if sources still reference it."""
    return _fmt(si_connections.delete_connection(_get_client(), connection_id))


@mcp.tool()
def si_test_connection(payload: dict) -> str:
    """Validate a connection payload without persisting it."""
    return _fmt(si_connections.test_connection(_get_client(), payload))


# --- SI sources -------------------------------------------------------------


@mcp.tool()
def si_list_sources() -> str:
    """List every data source visible to the caller (trimmed view)."""
    return _fmt(si_sources.list_sources(_get_client()))


@mcp.tool()
def si_get_source(source_id: str) -> str:
    """Read one data source including its schema description."""
    return _fmt(si_sources.get_source(_get_client(), source_id))


@mcp.tool()
def si_create_source(payload: dict) -> str:
    """Create a data source from a discovered schema payload."""
    return _fmt(si_sources.create_source(_get_client(), payload))


@mcp.tool()
def si_update_source(source_id: str, payload: dict) -> str:
    """Update a data source. Send the full document."""
    return _fmt(si_sources.update_source(_get_client(), source_id, payload))


@mcp.tool()
def si_delete_source(source_id: str) -> str:
    """Delete a data source."""
    return _fmt(si_sources.delete_source(_get_client(), source_id))


@mcp.tool()
def si_run_schema_discovery(connection_id: str, options: dict | None = None) -> str:
    """Trigger schema discovery against an existing connection."""
    return _fmt(si_sources.run_schema_discovery(_get_client(), connection_id, options))


# --- SI users / groups / tenants -------------------------------------------


@mcp.tool()
def si_list_users() -> str:
    """List every user in the active tenant."""
    return _fmt(si_users.list_users(_get_client()))


@mcp.tool()
def si_get_user(user_id: str) -> str:
    """Read one user."""
    return _fmt(si_users.get_user(_get_client(), user_id))


@mcp.tool()
def si_create_user(payload: dict) -> str:
    """Create a user."""
    return _fmt(si_users.create_user(_get_client(), payload))


@mcp.tool()
def si_list_groups() -> str:
    """List every group in the active tenant."""
    return _fmt(si_users.list_groups(_get_client()))


@mcp.tool()
def si_get_group(group_id: str) -> str:
    """Read one group."""
    return _fmt(si_users.get_group(_get_client(), group_id))


@mcp.tool()
def si_create_group(payload: dict) -> str:
    """Create a group."""
    return _fmt(si_users.create_group(_get_client(), payload))


@mcp.tool()
def si_get_tenant(tenant_id: str) -> str:
    """Read one tenant."""
    return _fmt(si_users.get_tenant(_get_client(), tenant_id))


@mcp.tool()
def si_create_tenant(payload: dict) -> str:
    """Create a tenant. Multi-tenant SI installs only."""
    return _fmt(si_users.create_tenant(_get_client(), payload))


# --- SI query ---------------------------------------------------------------


@mcp.tool()
def si_execute_query(source_id: str, sql: str, limit: int = 1000) -> str:
    """Run raw SQL against a data source. Useful for spot checks and admin queries."""
    return _fmt(si_query.execute_query(_get_client(), source_id, sql, limit))


@mcp.tool()
def si_explain_query(source_id: str, sql: str) -> str:
    """Return the engine's plan for the given SQL, without executing it."""
    return _fmt(si_query.explain_query(_get_client(), source_id, sql))


# --- Composer documentation -------------------------------------------------


@mcp.tool()
def search_composer_docs(query: str) -> str:
    """Full-text search across the bundled Composer reference snippets."""
    return docs_mod.search_composer_docs(query)


@mcp.tool()
def get_composer_api_reference(endpoint_path: str) -> str:
    """Return the bundled API reference entry for a Composer endpoint path."""
    return docs_mod.get_composer_api_reference(endpoint_path)


# --- Composer admin and embed ----------------------------------------------


@mcp.tool()
def composer_list_dashboards() -> str:
    """List every Composer dashboard."""
    return _fmt(composer_admin.list_dashboards(_get_client()))


@mcp.tool()
def composer_get_dashboard(dashboard_id: str) -> str:
    """Read one Composer dashboard document."""
    return _fmt(composer_admin.get_dashboard(_get_client(), dashboard_id))


@mcp.tool()
def composer_list_visuals() -> str:
    """List every Composer visual."""
    return _fmt(composer_admin.list_visuals(_get_client()))


@mcp.tool()
def composer_get_visual(visual_id: str) -> str:
    """Read one Composer visual document."""
    return _fmt(composer_admin.get_visual(_get_client(), visual_id))


@mcp.tool()
def composer_list_themes() -> str:
    """List every Composer theme."""
    return _fmt(composer_admin.list_themes(_get_client()))


@mcp.tool()
def composer_get_theme(theme_id: str) -> str:
    """Read one Composer theme document."""
    return _fmt(composer_admin.get_theme(_get_client(), theme_id))


@mcp.tool()
def composer_get_branding() -> str:
    """Return the active Composer branding configuration."""
    return _fmt(composer_admin.get_branding(_get_client()))


@mcp.tool()
def composer_list_scheduled_reports() -> str:
    """List every Composer scheduled report."""
    return _fmt(composer_admin.list_scheduled_reports(_get_client()))


@mcp.tool()
def composer_create_embed_token(payload: dict) -> str:
    """Mint a trusted-access embed token. Set payload.endpoint to 'pull' or 'push'."""
    return _fmt(composer_admin.create_embed_token(_get_client(), payload))


@mcp.tool()
def composer_api_call(method: str, suffix: str, body: dict | list | None = None, params: dict | None = None) -> str:
    """Generic Composer API call. Suffix is anything after `{composer_context}/api`, e.g. `/visuals/123`."""
    return _fmt(composer_admin.composer_api_call(_get_client(), method, suffix, body, params))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
