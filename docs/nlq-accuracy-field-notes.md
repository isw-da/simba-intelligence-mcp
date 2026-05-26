# NLQ accuracy: field notes for MCP consumers

Hard-won notes from a competitive PoV on getting reliable answers when an MCP
client (Claude etc.) consumes a Simba Intelligence deployment. Anonymised. The
full modelling playbook lives in the sibling `isw-da/composer-mcp` repo
(`NLQ_ACCURACY_PATTERNS.md`); this is the consumer-side summary plus the
endpoint facts.

## Core principle

The SI query agent is **deterministic when it selects a pre-computed answer
(a named metric, a row in a tiny table) and non-deterministic when it composes
a query** (choosing COUNT vs SUM, filtering a date, joining, set logic). Model so
the agent selects, not composes. This holds even on a high-quality backing model
(gemini-2.5-flash); it is intrinsic to one-shot generation, not a weak-model
artefact.

## Endpoint facts (for connecting a client)

- A live SI deployment exposes its MCP server on the ingress at **`/mcp`** (plus
  `/sse` and `/message`). It authenticates via **MCP OAuth** — the client
  auto-registers and obtains its own token.
- The static data-API key used for REST `/api/v1/*` calls does **NOT**
  authenticate against `/mcp`. Different auth path.
- Each deployment/tenant is separate: point the client at that tenant's `/mcp`.
- ISW ships the MCP server (it's part of the product); the customer connects an
  off-the-shelf MCP client to it. Nobody "builds a client" for the standard path.

## Modelling patterns that move accuracy (summary)

1. One fact entity per source (co-located grains cross-join and inflate).
2. A named custom metric for every canonical question (the agent matches and
   reads it; biggest lever after source structure).
3. Single-entity sources for attribute counts (multi-entity joins corrupt
   `count(*)`).
4. Periods as natural-language text ("April 2026"), not TIME (TIME triggers a
   default last-period filter the question can't override).
5. Pre-aggregate to the question's grain in a tiny source for counts/set logic.
6. Hide raw measures behind metrics — per single-entity count sources only;
   hiding a summed field on a fact source breaks its sum-metric.

## Source shape by question class

A lookup when scoping a model. Pick the source shape from the question shape;
the grain follows. Anonymised examples taken from a competitive PoV.

| Question class | Worked example | Source shape | Why |
|---|---|---|---|
| **Simple-lookup count** | "How many branches" | Single-entity. The dimension on its own, no join. | A join sample-aggregates the dimension; the count is wrong unless the dimension stands alone. |
| **Aggregate measure** | "Total successful value" | Multi-entity. One fact joined to the conformed dimension, plus a named metric. | One fact per source. The named metric is the single source of truth. |
| **Ranked measure** | "Top branches by successful value" | Same as aggregate; sort and limit at query time. | The agent picks the named metric and orders it. Its job is to select, not compose. |
| **Grouped count with filter** | "Enabled branches per region" | Single-entity dimension with the grouping column and status field on the same table; status mapped to plain values via a derived field. | Counting goes through the single-entity rule. The grouping column and the domain synonym both live on the same hub. |
| **Single-figure aggregate over many** | "Average successful value per branch" | Multi-entity, plus a named metric that returns one figure rather than a row per branch. | If the metric is not defined to roll up to a single figure, the agent returns a row per branch. Right data, wrong shape. |
| **Domain-synonym question** | "How many active branches" (no `active` column) | Derived field mapping raw codes to plain values, plus Field Metadata synonyms. | The agent does not guess what your word means. Teach it once in the source and the question resolves at once. |
| **Out-of-data question** | "EBITDA" (not in our data) | No source, no synthetic mapping. | A refusal is correct. If a plausible field is left findable, the agent will grab it. Trim the corpus. |

The rule that drops out: **shape is set by the grain of the data, not by
guessing which question someone will ask.** The same model handles a count and
a measure correctly because the dimension and the facts stay apart.

## Cautions (no-hallucination risk)

- **GROUP-BY-month pre-aggregated sources can error or FABRICATE** in the current
  build (observed: a perf month-totals source returned 123,456 for a month whose
  true value was 517,604,961). A source that invents a plausible number is a
  direct no-hallucination failure. Avoid that pattern until fixed; use the
  per-row source (honest undercount) or the verify/retry client loop.
- `sourceId` is advisory; the agent can defect to a foreign source on a shared
  tenant. Use a dedicated tenant; tenant rules do not reliably constrain it.

## What the MCP-client layer adds (and what it can't)

A capable client (Claude over this MCP) adds reasoning, decomposition, vocabulary
mapping, and verify/retry over the governed data layer. Measured lift on the
classes standalone fails: average-per-branch (wrong metric -> compose the right
two), and synonyms ("active" -> ENABLED). Best-of-N voting fixes host-noise and
one-off variance; it does **not** fix deterministic structural gaps (a missing
grain, an unbuilt dimension), those need modelling or a stronger model. Be honest
that it is a combination, not magic.
