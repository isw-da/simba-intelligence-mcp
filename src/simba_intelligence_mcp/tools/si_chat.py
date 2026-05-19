"""Chat and natural-language query tools.

`si_chat` is the headline SI capability: send a natural language question,
receive an answer streamed back over `/api/v1/chat/stream`. The MCP collapses
the SSE frames into a single string so the LLM can consume the result.

`si_chat_history` reads the per-user chat history endpoint, useful for
showing what the previous SI sessions did.
"""

from __future__ import annotations

from typing import Any

from ..client import SIClient, SIError


def si_chat(client: SIClient, question: str, source_id: str | None = None) -> str:
    """Ask SI a natural language question. Returns the final stitched answer.

    Args:
        question: the natural language prompt
        source_id: optional data source ID to scope the query. Omit to let SI
            pick from all sources the caller can see.
    """
    body: dict[str, Any] = {"question": question}
    if source_id:
        body["sourceId"] = source_id
    try:
        return client.stream_sse("/api/v1/chat/stream", body)
    except SIError as e:
        return f"Error {e.status}: {e}"


def si_chat_history(client: SIClient, limit: int = 20) -> Any:
    """Return the caller's recent chat history. Limit defaults to 20."""
    try:
        return client.get("/api/v1/chat/history", params={"limit": limit})
    except SIError as e:
        return {"error": e.status, "message": str(e)}
