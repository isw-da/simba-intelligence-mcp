# Composer documentation snippets

Curated, lightweight reference material for the Composer v25 REST surface.
Used by the `search_composer_docs` and `get_composer_api_reference` MCP
tools in `simba-intelligence-mcp`.

SI is built on top of Logi Composer (the SI Helm chart aliases the Composer
subchart as `discovery`), so this MCP carries the slice of the Composer
surface that SI users actually need: admin reads, embed tokens, branding,
and a generic API escape hatch.

For dashboard authoring at scale (widget layout, field links, time scope,
bulk import), the dedicated `isw-da/composer-mcp` server is the right
complement.
