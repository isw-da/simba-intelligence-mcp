"""SI data source management.

A "source" is the user-facing dataset that an SI chat session can target. It
carries the schema description that the LLM uses to translate a natural
language question into SQL.

Schema discovery (the action SI runs after wiring a new connection) is also
hosted here because it's the bridge between a connection and a usable source.
"""

from __future__ import annotations

from typing import Any

from ..client import SIClient, SIError


def list_sources(client: SIClient) -> Any:
    """List every data source visible to the caller. Returns the trimmed view."""
    try:
        raw = client.get("/discovery/api/sources")
    except SIError as e:
        return {"error": e.status, "message": str(e)}
    items = raw if isinstance(raw, list) else (raw.get("content") if isinstance(raw, dict) else [])
    out = []
    for s in items or []:
        if not isinstance(s, dict):
            continue
        out.append(
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "type": s.get("type"),
                "connectionName": s.get("connectionName"),
                "connectionId": s.get("connectionId"),
            }
        )
    return out


def get_source(client: SIClient, source_id: str) -> Any:
    """Read a single source. Returns the full document including schema description."""
    try:
        return client.get(f"/discovery/api/sources/{source_id}")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def create_source(client: SIClient, payload: dict) -> Any:
    """Create a new source. Typically follows a schema discovery run."""
    try:
        return client.post("/discovery/api/sources", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def update_source(client: SIClient, source_id: str, payload: dict) -> Any:
    """Update an existing source. Send the full document."""
    try:
        return client.put(f"/discovery/api/sources/{source_id}", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def delete_source(client: SIClient, source_id: str) -> Any:
    """Delete a source. Chat sessions that reference it will fail afterwards."""
    try:
        return client.delete(f"/discovery/api/sources/{source_id}")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def run_schema_discovery(client: SIClient, connection_id: str, options: dict | None = None) -> Any:
    """Trigger schema discovery against a connection. Returns the inferred schema.

    The options dict can include `includeTables`, `excludeTables`, `sampleSize`,
    etc. Defaults are sensible; omit to take them.
    """
    payload: dict[str, Any] = {"connectionId": connection_id}
    if options:
        payload.update(options)
    try:
        return client.post("/discovery/api/schema-discovery", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}
