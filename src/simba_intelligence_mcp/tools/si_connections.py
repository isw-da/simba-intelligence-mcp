"""SI Discovery connection management.

A "connection" is the binding to a backing database (Postgres, Snowflake,
Oracle, BigQuery, etc.) that SI's query engine talks to. Each connection can
back one or many "sources" (the user-facing dataset definitions).
"""

from __future__ import annotations

from typing import Any

from ..client import SIClient, SIError


def list_connections(client: SIClient) -> Any:
    """List every connection visible to the caller."""
    try:
        return client.get("/discovery/api/connections")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_connection(client: SIClient, connection_id: str) -> Any:
    """Read a single connection by ID."""
    try:
        return client.get(f"/discovery/api/connections/{connection_id}")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def create_connection(client: SIClient, payload: dict) -> Any:
    """Create a new connection. Payload shape varies by connector type.

    A typical Postgres payload looks like:
        {"name": "warehouse-pg",
         "type": "Postgresql",
         "params": {"host": "...", "port": 5432, "database": "...",
                    "username": "...", "password": "..."}}

    Inspect an existing connection of the same type first to get the exact
    parameter names for your connector.
    """
    try:
        return client.post("/discovery/api/connections", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def update_connection(client: SIClient, connection_id: str, payload: dict) -> Any:
    """Update an existing connection. Send the full document, not a patch."""
    try:
        return client.put(f"/discovery/api/connections/{connection_id}", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def delete_connection(client: SIClient, connection_id: str) -> Any:
    """Delete a connection. Fails if any sources still reference it."""
    try:
        return client.delete(f"/discovery/api/connections/{connection_id}")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def test_connection(client: SIClient, payload: dict) -> Any:
    """Validate a connection payload without persisting it."""
    try:
        return client.post("/discovery/api/connections/test", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}
