# Logi Composer v25 API reference (curated)

Bundled snippets for the most-used Composer endpoints. Sourced from the
official v25 docs (`https://logi-composer-v25.insightsoftware.com/hc/en-us`),
the team's internal notes, and the `composer-mcp` repository.

The MCP's `get_composer_api_reference(endpoint_path)` tool matches a request
to the section whose heading is the longest prefix of the supplied path.

All endpoints expect and return `application/vnd.composer.v3+json`. The base
path is `{host}{context_path}/api`, where `context_path` is `/composer`
(standalone) or `/discovery` (SI / Symphony bundle).

## /dashboards

- `GET    /dashboards`            list every dashboard the caller can read
- `GET    /dashboards/{id}`       read one dashboard document, including layout
- `POST   /dashboards`            create a dashboard (omit `unifiedBarCfgs` on POST; PUT it afterwards)
- `PUT    /dashboards/{id}`       full document replacement
- `DELETE /dashboards/{id}`       remove a dashboard

The dashboard layout is a 2-element path / params array in v25. Pre-v24 docs
that show 4-element layouts are stale.

## /visuals

- `GET    /visuals`               list visuals
- `GET    /visuals/{id}`          read one visual
- `POST   /visuals`               create a visual (bind to a sourceId)
- `PUT    /visuals/{id}`          replace a visual
- `DELETE /visuals/{id}`          remove a visual

`controlsCfg.timeControlCfg` overrides the default seven-day time window per
visual. Use `+$start_of_data`, `+$end_of_data`, `+$end_of_data_-1_week`,
`+$end_of_data_-1_month` for relative bounds.

## /sources

- `GET    /sources`               list every Composer source (distinct from SI Discovery sources)
- `GET    /sources/{id}`          read one source
- `POST   /sources`               create from a discovered schema
- `PUT    /sources/{id}`          replace
- `DELETE /sources/{id}`          remove

## /connections

- `GET    /connections`           list every Composer connection
- `GET    /connections/{id}`      read one connection
- `POST   /connections`           create
- `PUT    /connections/{id}`      replace
- `DELETE /connections/{id}`      remove

## /themes

- `GET    /themes`                list themes
- `GET    /themes/{id}`           read one theme
- `POST   /themes`                create a theme
- `PUT    /themes/{id}`           replace
- `DELETE /themes/{id}`           remove

## /branding

- `GET    /branding`              read the active branding (logo, palette, fonts)
- `PUT    /branding`              replace the branding document

## /scheduled-reports

- `GET    /scheduled-reports`     list scheduled reports
- `GET    /scheduled-reports/{id}` read one
- `POST   /scheduled-reports`     create
- `PUT    /scheduled-reports/{id}` replace
- `DELETE /scheduled-reports/{id}` remove

## /trusted-access/pull/tokens

- `POST   /trusted-access/pull/tokens`  mint a pull embed token

Used when Composer pulls user identity from the host on demand. Body shape
mirrors the Composer admin UI's embed wizard.

## /trusted-access/push/tokens

- `POST   /trusted-access/push/tokens`  mint a push embed token

Used when the host app asserts user identity into Composer. Higher trust
boundary; restrict the signing key carefully.

## /users

- `GET    /users`                 list users (admin only)
- `GET    /users/{id}`            read one user
- `POST   /users`                 create a user
- `PUT    /users/{id}`            replace
- `DELETE /users/{id}`            remove

Never mutate `/users/{id}` for the currently authenticated session. The
`composer-mcp` repo blocks this at the client layer after an internal
incident on 2026-05-07. This MCP does not enforce the guard yet; treat it as
a manual operator responsibility.

## /managed

The MDR (Managed Dashboards Resource) endpoints sit under `/managed/*`. They
are deliberately not exposed by this MCP. If you need MDR, drive it
manually outside any automation surface.

## CSRF and bundled Symphony

When Composer is bundled inside SI / Symphony (served at `/discovery`), Spring
Security enforces CSRF on every state-changing request. The error message
"Your user session has expired" is misleading; it actually means the
`X-CSRF-TOKEN` header is missing. Pass the token (read from the
`<meta name="_csrf">` tag in a logged-in browser session) via the
`COMPOSER_CSRF_TOKEN` environment variable.
