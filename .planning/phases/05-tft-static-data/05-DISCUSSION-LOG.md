# Phase 5: TFT Static Data - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 05-tft-static-data
**Areas discussed:** Data Sources, Chunk Strategy, Cache Strategy, Metadata Filtering

---

## Area 1: Data Sources

|| Option | Description | Selected |
|--------|---------|---------|---------|
| Riot CDN (ddragon + gitcdn) | Download from Riot Data Dragon CDN + CommunityDragon CDN — official, stable, no API keys | ✓ |
| Riot API + ddragon | Riot API (web) for version check + ddragon for data files | |
| CommunityDragon only | Only CommunityDragon — sufficient for static data, no version check | |

**User's choice:** Riot CDN (ddragon + gitcdn) — recommended default
**Notes:** Official CDN is stable and doesn't require API keys. Version check via `versions.json` CDN endpoint.

---

## Area 2: Chunk Strategy

|| Option | Description | Selected |
|--------|---------|---------|---------|
| Per-type (4 chunks) | 1 chunk per category (champions/traits/items/augments) — simple, fewer chunks | ✓ |
| Per-unit (200+ chunks) | Each champion/item/augment = separate chunk — more retrieval precision | |
| Hybrid | Unit-level for champions/augments, type-level for traits/items | |

**User's choice:** Per-type — recommended default
**Notes:** 4 chunks total per patch. Chunk size ~2000 chars; larger types split if needed. Per-unit deferred to Phase v2 for more granular retrieval.

---

## Area 3: Cache Strategy

|| Option | Description | Selected |
|--------|---------|---------|---------|
| Per-patch folder | `~/.tft-copilot/cache/{patch}/` — versioned folders, easy rollback | ✓ |
| Single global cache | 1 cache file, check version before downloading | |
| No cache | Always download — slow but always fresh | |

**User's choice:** Per-patch folder — recommended default
**Notes:** Follows existing `TFT_PATCH_CACHE` path pattern from `patch_refresh.py`. Enables rollback to older patches.

---

## Area 4: Metadata Filtering

|| Option | Description | Selected |
|--------|---------|---------|---------|
| SQL WHERE on JSONB | Filter via `metadata->>'patch'` in SQL WHERE clause | ✓ |
| Source-based | Partition by source string, filter with LIKE | |
| Prompt-based | Send patch version in prompt, model self-filters | |

**User's choice:** SQL WHERE on JSONB — recommended default
**Notes:** Follows existing metadata JSONB pattern from Phase 4. Route accepts optional `?patch=` param.

---

## Claude's Discretion

The following were left to Claude's discretion (user did not specify):

- Exact CDN URLs (Riot Data Dragon + CommunityDragon structure for Set 17)
- Number of chunks per type if content exceeds 2000 chars (split into 2)
- Whether to use `ON CONFLICT` or `DELETE + INSERT` for re-ingest
- Batch embedding size (follows existing BATCH_SIZE=16 pattern)

---

## Deferred Ideas

- Per-unit chunking — Phase v2 for more granular retrieval
- TFT patch auto-detection via Riot API webhooks — Phase 6 automation scope
- TFT data in Coach mode retrieval — Phase 5 integration with Phase 4 retrieval
