# Tests

## Automated

```bash
uv run pytest
```

Runs the documentation layer smoke tests. No SI deployment required.

## Manual end to end checklist

Run these against a live SI (local kind cluster or hosted) after starting
the MCP:

1. `si_health` returns `{"status": "UP"}` (or equivalent).
2. `si_user` returns the authenticated user's profile.
3. `si_list_sources` returns the data sources visible to the caller.
4. `si_chat_query` with a simple question against a known source returns a
   non-empty answer.
5. `si_list_connections` returns the Discovery connections visible to the
   caller (or an empty list on a fresh install).

Document each pass in the deal notes / readiness check, not here.
