# STATE: TFT Local Copilot

**Project:** TFT Local Copilot
**Last updated:** 2026-04-23

---

## Project Reference

**Core Value:** A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem. **v1.4 transforms this from a search tool into an intelligent knowledge companion.**

**Current Milestone:** v1.4 Smart & Polished — in progress

---

## Current Position

**Active Phase:** Phase 12 — UI/UX Core Redesign (plans verified 2026-04-23)

**Phase 11 Status:** Complete — 486 nodes, 500 edges, 23 tests passing

**Phase 12 Wave Structure:**
```
Wave 1 (parallel-safe): 12-01 (MessageList), 12-03 (CompCard), 12-04 (ChatShell)
Wave 2 (after 12-01):   12-02 (CitationCard v2), 12-05 (EmptyState)
```

**Milestone Progress:**
```
✅ v1.0 MVP — Phases 1-7 (shipped 2026-04-22)
✅ v1.1 TFT Meta Mastery — Phase 8 (shipped 2026-04-22)
✅ v1.2 MetaTFT Real-time Intelligence — Phase 9 (shipped 2026-04-23)
✅ v1.3 Hardening & Polish — Phase 10 (shipped 2026-04-23)
🔄 v1.4 Smart & Polished — Phases 11-14 (Phase 11 complete, Phase 12 context gathered)
```

---

## v1.4 "Smart & Polished" — Vision

### Problem Statement

The current system answers questions but doesn't *understand* TFT entities. It retrieves text chunks, not structured knowledge. Three concrete pain points:

1. **Flat responses:** "What items for Briar?" returns a wall of text. Not structured, not cross-linked.
2. **UI overflow:** Long messages stretch the container, breaking layout alignment.
3. **Sparse knowledge:** Only 32 chunks in the DB. 252 augments and 59 champions are not in the vector store.

### Solution Architecture

```
User Query
    │
    ▼
┌─────────────────────┐
│  Smart Query Router  │ ← Phase 13 (SMART-04)
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│Knowledge│  │   RAG   │  │ MetaTFT  │
│ Graph   │  │ Pipeline│  │  Data    │
│(NetworkX)│  │(vector) │  │(scraped) │
└────┬────┘  └────┬────┘  └────┬────┘
     │             │             │
     └─────────────┴─────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  LLM Response  │
            │(entity markers)│
            └───────┬───────┘
                    │
                    ▼
            ┌─────────────────┐
            │ Frontend Entity │
            │ Cards + CompCard│
            └─────────────────┘
```

### Key Design Decisions for v1.4

| Decision | Rationale | Status |
|----------|-----------|--------|
| NetworkX for knowledge graph | Fast, Python-native, easy to serialize | ✅ Planned (Phase 11) |
| Entity JSON markers in LLM output | No prompt overhead, easy to parse | ✅ Planned (Phase 13) |
| Knowledge Graph as primary for entity queries | Graph traversal is faster than vector search for direct entity lookups | ✅ Planned (Phase 13) |
| Tailwind-only CompCard | Replace inline styles for maintainability | ✅ Planned (Phase 12) |
| Streaming citations (SSE events) | Progressive reveal improves perceived latency | ✅ Planned (Phase 14) |

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| v1.0 Requirements mapped | 35/35 | 100% coverage |
| v1.1 Requirements | 5/5 | PATCH-01..05 complete |
| v1.2 Requirements (META) | 5/5 | META-01..05 complete |
| v1.3 Requirements (HARD) | 5/5 | HARD-01..05 complete |
| v1.4 Requirements | 19/19 | KNOW-01..04, UI-01..05, SMART-01..05, RAG2-01..05 |
| Total Phases shipped | 10 | Phases 1-10 all shipped |
| **v1.4 DB chunk target** | **≥ 500** | Currently ~44 chunks |

---

## Hardware Context

| Resource | Capacity | Usage |
|----------|---------|-------|
| RAM | 64GB | Full system |
| VRAM | 12GB (RTX 4070 Ti SUPER) | Chat + Embedding models |
| Chat model | qwen3:1.7b | ~1.4GB VRAM |
| Embedding model | qwen3-embedding:4b | ~2.5GB VRAM (2560 dims → 1024 truncated) |
| **VRAM headroom for v1.4** | ~8GB free | Could upgrade to qwen3:8b in future |

---

## Stack Summary

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 19 + Vite 6 + Tailwind 4 | Chat UI — being redesigned in Phase 12 |
| Backend | FastAPI + Uvicorn | API orchestration + Knowledge Graph |
| LLM | Ollama native (Windows) | qwen3:1.7b + qwen3-embedding:4b |
| Database | Supabase local CLI (pgvector/HNSW) | 1024-dim embeddings, 44→500+ chunks in v1.4 |
| Automation | n8n (Docker) | Scheduled workflows |
| Knowledge | Obsidian vault + JSON data packs | Markdown notes + verified TFT data |
| **NEW** Knowledge Graph | NetworkX | In-memory graph for cross-entity traversal (Phase 11) |
| TFT Data | Riot CDN + CommunityDragon + MetaTFT + User-verified JSON | Set 17 Space Gods, Patch 17.1 |

---

## Key Decisions (Locked)

| Decision | Rationale | Status |
|----------|-----------|--------|
| Ollama native (not containerized) | GPU passthrough on Windows | ✅ Locked |
| 1024-dim embeddings | HNSW index limit 2000 dims, qwen3-embedding:4b truncates to 1024 | ✅ Locked |
| Supabase local CLI | Postgres + pgvector without Docker complexity | ✅ Locked |
| 3-mode chat (Normal/RAG/Coach) | TFT policy compliance | ✅ Locked |
| SSE for streaming | Sufficient for one-way streaming | ✅ Locked |
| In-memory LRU cache | MVP scale doesn't need Redis | ✅ Locked |
| Bearer token auth | Defense in depth | ✅ Locked |
| ngrok dropped | 100% local, no remote access needed | ✅ Locked |
| RLS disabled | Local-only, risk accepted | ✅ Locked |
| NetworkX for knowledge graph | Fast, Python-native, easy to serialize/deserialize | ✅ Planned (Phase 11) |
| Entity JSON markers | LLM outputs structured JSON inline; frontend parses and renders cards | ✅ Planned (Phase 13) |
| Graph-first routing | Knowledge Graph for direct entity queries; RAG for complex questions | ✅ Planned (Phase 13) |

---

## Data Files (Verified)

User has provided verified data files for v1.4 ingest:

| File | Entities | Used in Phase |
|------|---------|--------------|
| `augments_full_user_verified.json` | 252 augments (Silver/Gold/Prismatic) | 14 (RAG2-04) |
| `traits_full_user_verified.json` | 30+ traits with champions + breakpoints | 11 (KNOW-01), 14 (RAG2-04) |
| `items_effects_expanded_set17.json` | 45+ items with effect text | 11 (KNOW-01), 14 (RAG2-04) |
| `tft_set17_patch17_1_deep_pack_v4_user_verified.json` | 59 champions + traits + systems | 11 (KNOW-01), 14 (RAG2-04) |
| `tft_set17_patch17_1_enhanced_pack.json` | 9 Space Gods + Realm of the Gods | 11 (KNOW-01), 14 (RAG2-04) |
| `tft_set17_patch17_1_data_pack.json` | Full champion roster + abilities + meta | 11 (KNOW-01), 14 (RAG2-04) |
| `rolling_odds_user_verified.json` | Rolling odds by level (verified) | 11 (KNOW-01), 14 (RAG2-04) |

---

## Known Issues

### UI Issues (To Fix in Phase 12)

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Message bubble overflow | No `max-width` enforcement + missing `min-w-0` on flex containers | UI-01 |
| CitationCard truncates | `line-clamp-3` + no expand state | UI-02 |
| CompCard inline styles | Mixed inline/Tailwind, hard to maintain | UI-03 |
| No mobile layout | No responsive breakpoints | UI-04 |
| Poor streaming UX | Basic typing indicator, no progressive reveal | UI-05 |

### Security (Acknowledged)

- ⚠️ **RLS disabled on DB tables** — accepted risk for local-only deployment

---

## Session Continuity

### For Next Session

When starting v1.4 Phase 11:
1. Run health checks:
   ```powershell
   ollama ps
   npx supabase status
   curl http://localhost:8000/api/health
   curl http://localhost:8000/api/health/gpu
   curl http://localhost:8000/api/patch/status
   ```
2. Verify the 7 verified data files are in the project root
3. Start Phase 11 with `$gsd-plan-phase 11`

### What v1.4 Changes

| Before v1.4 | After v1.4 |
|-------------|-------------|
| Text chunks in DB (~44) | Structured chunks by entity type (500+) |
| Flat markdown text responses | Rich entity cards (ChampionProfile, ItemCard, TraitCard, AugmentCard) |
| Keyword search | Knowledge graph traversal + vector search hybrid |
| Citation cards at end of response | Streaming citations that appear progressively |
| Single-column layout, overflow bugs | Responsive layout with proper overflow handling |
| 3 modes (Normal/RAG/Coach) | Same 3 modes, but each delivers smarter, cross-linked answers |
| 32 ingested TFT data chunks | 500+ chunks covering all Set 17 entities |

---

## Accumulated Context

### v1.4 Planned Features

**Phase 11: Knowledge Graph (KNOW-01..04)**
- NetworkX graph with Champion, Item, Trait, Augment, God, System nodes
- Edges: HAS_TRAIT, BUILDS_FROM, ITEM_FOR_CHAMPION, SYNERGIZES, TRAIT_BREAKPOINT
- API: GET /api/graph/query, GET /api/graph/neighbors/{entity}, POST /api/graph/ingest
- Auto-reload on patch ingest + hot-reload endpoint

**Phase 12: UI/UX Core Redesign (UI-01..05)**
- Fix message overflow: `min-w-0`, `max-w-[70%]`, `overflow-wrap: break-word`
- CitationCard v2: expandable, collapsible, source filter, copy button
- CompCard Tailwind migration: replace inline styles, full type safety
- Responsive: mobile sidebar drawer, tablet 2-column citations
- Loading states: skeleton loaders, streaming cursor, welcome screen

**Phase 13: Smart Chat Engine (SMART-01..05)**
- LLM emits entity JSON markers: `{"type": "champion", "name": "Briar", ...}`
- Frontend parser renders: ChampionProfile, ItemCard, TraitCard, AugmentCard
- Smart reply suggestions: context-aware chips from knowledge graph
- Query router: graph-first for entities, rag-fallback for complex questions
- Coach enhancements: pivot fallback chain, in-game scenario presets ([fast8], [hyperoll])

**Phase 14: RAG 2.0 + Full Data Ingest (RAG2-01..05)**
- Entity type metadata filtering: champion, item, trait, augment, system
- Heuristic reranking: patch_priority × entity_priority × recency_boost
- Streaming citations: citation_start/citation_progress/citation_end SSE events
- Full ingest: 252 augments + 59 champions + 45+ items + 30+ traits + systems
- Obsidian file watcher for real-time reactive sync

---

*State tracked: 2026-04-23*
*Last updated: 2026-04-23 — Phase 12 plans verified, wave structure established*
