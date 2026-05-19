"""HTTP client for Simba Intelligence.

One client speaks to two related path namespaces on the same host:

  - `/api/v1/*`        the SI main app (chat stream, user, healthz)
  - `/discovery/api/*` the Discovery / Query Engine REST API used by the
                       admin UI for connections, sources, users, groups,
                       tenants, permissions, connectors, schema discovery

Auth model:
  1. Static API key in `SI_API_KEY` (preferred for local dev and CI). Sent as
     `Authorization: Bearer <key>`.
  2. Username and password in `SI_USERNAME` / `SI_PASSWORD`. Call the
     `authenticate()` tool first; the bearer is cached on the singleton
     client for the rest of the MCP session.

The client never logs credentials. It deliberately keeps responses as Python
dicts / lists (parsed JSON) so the tool layer can shape the output.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class SIConfig:
    base_url: str = field(default_factory=lambda: os.environ.get("SI_BASE_URL", "http://localhost:8080"))
    api_key: str = field(default_factory=lambda: os.environ.get("SI_API_KEY", ""))
    username: str = field(default_factory=lambda: os.environ.get("SI_USERNAME", ""))
    password: str = field(default_factory=lambda: os.environ.get("SI_PASSWORD", ""))
    timeout: float = field(default_factory=lambda: float(os.environ.get("SI_HTTP_TIMEOUT", "60")))
    # Composer context path under the SI host. SI bundles Composer behind
    # `/discovery`; standalone Composer installations expose `/composer`.
    composer_context: str = field(
        default_factory=lambda: os.environ.get("SI_COMPOSER_CONTEXT", "/discovery")
    )

    def normalise(self) -> "SIConfig":
        self.base_url = self.base_url.rstrip("/")
        self.composer_context = "/" + self.composer_context.strip("/") if self.composer_context else "/discovery"
        return self


class SIError(RuntimeError):
    """Raised when the SI API returns a non-2xx response."""

    def __init__(self, status: int, message: str, body: Any = None) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.body = body


class SIClient:
    """Thin httpx wrapper. One instance per MCP process, reused across tools."""

    def __init__(self, cfg: SIConfig | None = None) -> None:
        self.cfg = (cfg or SIConfig()).normalise()
        # Cached bearer obtained via authenticate(). Falls back to api_key.
        self._session_bearer: str | None = None
        self._client = httpx.Client(
            base_url=self.cfg.base_url,
            timeout=httpx.Timeout(self.cfg.timeout),
            follow_redirects=False,
        )

    @property
    def bearer(self) -> str:
        return self._session_bearer or self.cfg.api_key

    def close(self) -> None:
        self._client.close()

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.bearer:
            h["Authorization"] = f"Bearer {self.bearer}"
        if extra:
            h.update(extra)
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        """Make an HTTP request and return parsed JSON (or raw text fallback).

        `path` must include the namespace (e.g. `/discovery/api/sources`).
        """
        if not path.startswith("/"):
            path = "/" + path
        resp = self._client.request(
            method.upper(),
            path,
            json=json_body,
            params=params,
            headers=self._headers(extra_headers),
        )
        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("message") or body.get("error") or resp.text[:300]
            except Exception:
                body = resp.text[:500]
                msg = body
            raise SIError(resp.status_code, msg, body)
        if not resp.content:
            return None
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype:
            return resp.json()
        # Some endpoints return text or SSE. Return as a string for the tool to handle.
        return resp.text

    def stream_sse(self, path: str, json_body: dict[str, Any]) -> str:
        """POST a request that returns a server-sent event stream and stitch the message frames.

        Used for `/api/v1/chat/stream` and any other SSE-style endpoint. Returns
        the concatenated `message` field across `data:` frames.
        """
        if not path.startswith("/"):
            path = "/" + path
        with self._client.stream(
            "POST",
            path,
            json=json_body,
            headers=self._headers(),
        ) as resp:
            if resp.status_code >= 400:
                raw = resp.read().decode(errors="replace")
                raise SIError(resp.status_code, raw[:300], raw)
            chunks: list[str] = []
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = line[len("data: "):].strip()
                if not payload or payload in {"[DONE]", "Starting chat response", "Chat response completed"}:
                    continue
                try:
                    msg = json.loads(payload)
                except json.JSONDecodeError:
                    chunks.append(payload)
                    continue
                txt = msg.get("message") if isinstance(msg, dict) else None
                if isinstance(txt, str) and not txt.startswith("[{"):
                    chunks.append(txt)
        return "".join(chunks) if chunks else "(no streamed content)"

    # Convenience wrappers

    def get(self, path: str, **kw) -> Any:
        return self.request("GET", path, **kw)

    def post(self, path: str, json_body: Any | None = None, **kw) -> Any:
        return self.request("POST", path, json_body=json_body, **kw)

    def put(self, path: str, json_body: Any | None = None, **kw) -> Any:
        return self.request("PUT", path, json_body=json_body, **kw)

    def patch(self, path: str, json_body: Any | None = None, **kw) -> Any:
        return self.request("PATCH", path, json_body=json_body, **kw)

    def delete(self, path: str, **kw) -> Any:
        return self.request("DELETE", path, **kw)

    def authenticate(self, base_url: str | None, username: str, password: str) -> str:
        """Exchange username and password for a bearer, cached for this MCP session.

        SI exposes a login endpoint at `/api/auth/login` on the main app and a
        fallback at `/discovery/api/login` for the Discovery context. We try
        both. The returned token is cached as `self._session_bearer` so every
        subsequent tool call goes out with `Authorization: Bearer <token>`.
        """
        if base_url:
            self.cfg.base_url = base_url.rstrip("/")
            self._client.base_url = httpx.URL(self.cfg.base_url)
        body = {"username": username, "password": password}
        token: str | None = None
        last_error: SIError | None = None
        for path in ("/api/auth/login", "/discovery/api/login", "/api/v1/auth/login"):
            try:
                resp = self.request("POST", path, json_body=body)
            except SIError as e:
                last_error = e
                continue
            if isinstance(resp, dict):
                token = resp.get("token") or resp.get("access_token") or resp.get("accessToken")
                if token:
                    break
        if not token:
            raise last_error or SIError(401, "No login endpoint accepted the credentials.")
        self._session_bearer = token
        return token
