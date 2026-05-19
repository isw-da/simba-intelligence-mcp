"""Generic SI Discovery API helpers.

The Discovery API surface is huge. Rather than hand-rolling every endpoint we
expose:

  - `si_api_call(method, path, body, params)` for arbitrary requests
  - Dedicated tools (in sibling modules) for the most common operations
  - `si_health` / `si_version` / `si_user` introspection helpers

The path argument is taken verbatim (after a leading-slash check). Pass the
full namespace, e.g. `/discovery/api/sources` or `/api/v1/healthz`.
"""

from __future__ import annotations

import json
from typing import Any

from ..client import SIClient, SIError


def si_api_call(
    client: SIClient,
    method: str,
    path: str,
    body: dict | list | None = None,
    params: dict | None = None,
) -> Any:
    """Make an arbitrary SI request. Returns parsed JSON, text, or an error dict."""
    try:
        return client.request(method, path, json_body=body, params=params)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def si_health(client: SIClient) -> Any:
    """Hit `GET /api/v1/healthz`. Returns the body or an error dict."""
    return si_api_call(client, "GET", "/api/v1/healthz")


def si_version(client: SIClient) -> Any:
    """Hit `GET /discovery/api/version` (and fall back to `/api/v1/version`)."""
    primary = si_api_call(client, "GET", "/discovery/api/version")
    if isinstance(primary, dict) and primary.get("error"):
        return si_api_call(client, "GET", "/api/v1/version")
    return primary


def si_user(client: SIClient) -> Any:
    """Return the currently authenticated user. Tries main app first, then Discovery."""
    primary = si_api_call(client, "GET", "/api/v1/user")
    if isinstance(primary, dict) and primary.get("error"):
        return si_api_call(client, "GET", "/discovery/api/user")
    return primary


def si_llm_config(client: SIClient) -> Any:
    """Return the active LLM configuration. Useful for diagnosing BYOLLM setups."""
    return si_api_call(client, "GET", "/discovery/api/llm/config")


def si_list_connectors(client: SIClient) -> Any:
    """List installed EDC / Discovery connectors."""
    return si_api_call(client, "GET", "/discovery/api/connectors")


def si_list_tenants(client: SIClient) -> Any:
    """List tenants visible to the caller."""
    return si_api_call(client, "GET", "/discovery/api/tenants")


def si_list_permissions(client: SIClient) -> Any:
    """List permissions defined in the active tenant."""
    return si_api_call(client, "GET", "/discovery/api/permissions")


def si_pretty(value: Any) -> str:
    """Format any tool return as a JSON string for the MCP transport."""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, indent=2, default=str)
    except Exception:
        return str(value)
