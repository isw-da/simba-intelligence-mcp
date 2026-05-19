"""Logi Composer admin, embed, and documentation helpers.

SI is built on top of Logi Composer. The SI Helm chart aliases the Composer
subchart as `discovery`, EDC connectors live in Composer, and the SI
reference guides routinely reference Composer admin patterns. This module
exposes the slice of the Composer REST surface that SI operators and SE
teams reach for in practice:

  - List and read dashboards, visuals, themes, scheduled reports
  - Read the active branding document
  - Mint trusted-access embed tokens (pull and push)
  - A generic `composer_api_call` escape hatch

For dashboard authoring at scale (widget layout, field links, time scope,
bulk import), the dedicated `isw-da/composer-mcp` server is the right tool.
The two servers coexist for different audiences.

All Composer endpoints expect and return `application/vnd.composer.v3+json`.
The base path is `{base_url}{composer_context}/api`, where
`composer_context` is `/discovery` when Composer is bundled inside SI /
Symphony, or `/composer` for a standalone install. Configure via the
`SI_COMPOSER_CONTEXT` environment variable.
"""

from __future__ import annotations

from typing import Any

from ..client import SIClient, SIError

VENDOR_MEDIA_TYPE = "application/vnd.composer.v3+json"


# --- HTTP helpers -----------------------------------------------------------


def _ctx(client: SIClient, suffix: str) -> str:
    """Prefix a Composer API suffix with the configured context path."""
    if not suffix.startswith("/"):
        suffix = "/" + suffix
    return f"{client.cfg.composer_context}/api{suffix}"


def _composer_headers() -> dict[str, str]:
    return {"Accept": VENDOR_MEDIA_TYPE, "Content-Type": VENDOR_MEDIA_TYPE}


def _unwrap(data: Any) -> Any:
    """Composer list endpoints sometimes return {content: [...]}, sometimes raw."""
    if isinstance(data, dict):
        for key in ("content", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return data


# --- Admin / embed tools (10) ----------------------------------------------


def list_dashboards(client: SIClient) -> Any:
    try:
        return _unwrap(client.get(_ctx(client, "/dashboards"), extra_headers=_composer_headers()))
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_dashboard(client: SIClient, dashboard_id: str) -> Any:
    try:
        return client.get(_ctx(client, f"/dashboards/{dashboard_id}"), extra_headers=_composer_headers())
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def list_visuals(client: SIClient) -> Any:
    try:
        return _unwrap(client.get(_ctx(client, "/visuals"), extra_headers=_composer_headers()))
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_visual(client: SIClient, visual_id: str) -> Any:
    try:
        return client.get(_ctx(client, f"/visuals/{visual_id}"), extra_headers=_composer_headers())
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def list_themes(client: SIClient) -> Any:
    try:
        return _unwrap(client.get(_ctx(client, "/themes"), extra_headers=_composer_headers()))
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_theme(client: SIClient, theme_id: str) -> Any:
    try:
        return client.get(_ctx(client, f"/themes/{theme_id}"), extra_headers=_composer_headers())
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def get_branding(client: SIClient) -> Any:
    """Return the active branding configuration (logo, palette, fonts)."""
    try:
        return client.get(_ctx(client, "/branding"), extra_headers=_composer_headers())
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def list_scheduled_reports(client: SIClient) -> Any:
    try:
        return _unwrap(client.get(_ctx(client, "/scheduled-reports"), extra_headers=_composer_headers()))
    except SIError as e:
        return {"error": e.status, "message": str(e)}


def create_embed_token(client: SIClient, payload: dict) -> Any:
    """Mint an embed token. Payload mirrors the trusted-access endpoint.

    For pull tokens (Composer reaches out to a backend on behalf of the
    embedded user), POST to `/api/trusted-access/pull/tokens`.
    For push tokens (the host app pushes user identity into Composer), POST
    to `/api/trusted-access/push/tokens`.

    Pass `{"endpoint": "pull" | "push", "body": {...}}` to choose. Defaults
    to pull when omitted.
    """
    endpoint = payload.get("endpoint", "pull")
    body = payload.get("body") or {}
    suffix = f"/trusted-access/{endpoint}/tokens"
    try:
        return client.post(_ctx(client, suffix), json_body=body, extra_headers=_composer_headers())
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}


def composer_api_call(
    client: SIClient,
    method: str,
    suffix: str,
    body: dict | list | None = None,
    params: dict | None = None,
) -> Any:
    """Generic escape hatch. Calls `{composer_context}/api{suffix}` with the vendor media type."""
    try:
        return client.request(
            method,
            _ctx(client, suffix),
            json_body=body,
            params=params,
            extra_headers=_composer_headers(),
        )
    except SIError as e:
        return {"error": e.status, "message": str(e), "body": e.body}
