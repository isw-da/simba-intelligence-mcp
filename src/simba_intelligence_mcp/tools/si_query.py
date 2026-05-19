"""SI query execution tools.

`execute_query` runs a SQL statement through the Discovery query engine,
respecting any row-level security policies configured against the active
tenant. Useful for spot-checking what SI actually executes after the natural
language translation step, or for direct admin queries that bypass the chat
interface.
"""

from __future__ import annotations

from typing import Any

from ..client import SIClient, SIError


def execute_query(
    client: SIClient,
    source_id: str,
    sql: str,
    limit: int = 1000,
) -> Any:
    """Execute a SQL statement against the named source.

    Args:
        source_id: the SI data source ID (see `list_sources`)
        sql: raw SQL accepted by the connector's dialect
        limit: row cap, default 1000
    """
    payload = {"sourceId": source_id, "sql": sql, "limit": limit}
    try:
        return client.post("/discovery/api/query/execute", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def explain_query(client: SIClient, source_id: str, sql: str) -> Any:
    """Return the engine's plan for the given SQL, without executing it."""
    payload = {"sourceId": source_id, "sql": sql}
    try:
        return client.post("/discovery/api/query/explain", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}
