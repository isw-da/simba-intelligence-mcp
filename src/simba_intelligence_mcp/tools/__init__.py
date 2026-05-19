"""SI tool implementations.

The server module imports each submodule and binds its functions as MCP
tools. Each function takes an SIClient as its first argument and returns
plain Python data (dicts, lists, strings).
"""

from . import composer_admin, si_admin, si_chat, si_connections, si_query, si_sources, si_users

__all__ = [
    "composer_admin",
    "si_admin",
    "si_chat",
    "si_connections",
    "si_sources",
    "si_users",
    "si_query",
]
