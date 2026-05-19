"""SI user, group, and tenant management."""

from __future__ import annotations

from typing import Any

from ..client import SIClient, SIError


def list_users(client: SIClient) -> Any:
    try:
        return client.get("/discovery/api/users")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_user(client: SIClient, user_id: str) -> Any:
    try:
        return client.get(f"/discovery/api/users/{user_id}")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def create_user(client: SIClient, payload: dict) -> Any:
    """Create a new user. Payload typically includes name, email, role."""
    try:
        return client.post("/discovery/api/users", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def list_groups(client: SIClient) -> Any:
    try:
        return client.get("/discovery/api/groups")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_group(client: SIClient, group_id: str) -> Any:
    try:
        return client.get(f"/discovery/api/groups/{group_id}")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def create_group(client: SIClient, payload: dict) -> Any:
    try:
        return client.post("/discovery/api/groups", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def list_tenants(client: SIClient) -> Any:
    try:
        return client.get("/discovery/api/tenants")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_tenant(client: SIClient, tenant_id: str) -> Any:
    try:
        return client.get(f"/discovery/api/tenants/{tenant_id}")
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def create_tenant(client: SIClient, payload: dict) -> Any:
    """Create a tenant. Multi-tenant SI installs only."""
    try:
        return client.post("/discovery/api/tenants", json_body=payload)
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}
