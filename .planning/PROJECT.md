# TFT Local Copilot

## What This Is

A local-first AI copilot for Teamfight Tactics (TFT Set 17 Space Gods, Patch 17.1) that runs entirely on the user's machine — no cloud APIs, no external dependencies. **v1.4 transforms this from a search tool into an intelligent knowledge companion.** Stack: React chat UI + FastAPI backend + Ollama local LLM + Supabase pgvector RAG + Obsidian knowledge source + **NetworkX Knowledge Graph**.

**Three chat modes:** Normal (free chat), RAG (retrieve from notes + patch data), Coach (2-3 lines of play with trade-off analysis). Each mode delivers smarter, cross-linked answers through the Knowledge Graph and entity cards.

## Core Value

A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers that understand the relationships between champions, items, traits, and augments. Not just keyword matching — reasoned, interconnected knowledge.

## Requirements

### Validated

- ✅ Local LLM chat with streaming responses (Ollama + qwen3:1.7b) — v1.0
- ✅ Three mode system: Normal / RAG / Coach — v1.0
- ✅ RAG retrieval from Obsidian Markdown vault + TFT patch notes — v1.0
- ✅ Hybrid search (full-text + semantic via pgvector HNSW) — v1.0
- ✅ TFT static data ingestion (patch 17.1, 32 chunks) — v1.0
- ✅ Reactive chat UI (React + Vite + Tailwind) — v1.0
- ✅ FastAPI backend with session/message persistence — v1.0
- ✅ Obsidian vault ingest pipeline with chunking + embedding — v1.0
- ✅ n8n automation for scheduled ingest + patch monitoring — v1.0
- ✅ TTL-LRU embedding cache (30-min, 500 entries) — v1.0
- ✅ GPU memory monitoring (frontend display) — v1.0
- ✅ 20-question smoke test: 60/60 PASS — v1.0
- ✅ Patch state in DB with `patch_info` table — v1.1
- ✅ Backend patch status API (GET /api/patch/status) — v1.1
- ✅ Auto-scrape patch notes API (POST /api/ingest/patch-notes) — v1.1
- ✅ n8n patch monitoring workflow (active) + Discord notifications — v1.1
- ✅ Frontend patch version display + staleness badge — v1.1
- ✅ MetaTFT scraper + CompCard rendering — v1.2
- ✅ Session switch spinner + 60s timeout + Toast system — v1.3

### Active (v1.4)

- [ ] Phase 11: Knowledge Graph — NetworkX graph with Champion/Item/Trait/Augment/God/System nodes (KNOW-01..04)
- [ ] Phase 12: UI/UX Core Redesign — overflow fix, CitationCard v2, CompCard Tailwind, responsive breakpoints (UI-01..05)
- [ ] Phase 13: Smart Chat Engine — entity JSON markers, inline cards, smart suggestions, query routing (SMART-01..05)
- [ ] Phase 14: RAG 2.0 — entity-type metadata filtering, heuristic reranking, streaming citations, full ingest 500+ chunks (RAG2-01..05)

### Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time opponent scouting / overlay | Violates Riot TFT policy |
| In-game overlay or HUD | Violates TFT policy; dictates decisions |
| Automated "best action" button or macro | Removes player agency |
| Cloud API dependencies | Must remain fully local |
| Auth / user management | Single local user, no multi-user need |
| Non-Windows targets | MVP is Windows-only |
| WebSocket instead of SSE | SSE is sufficient for streaming |
| Redis or distributed cache | In-memory LRU sufficient for MVP |
| Cross-encoder reranking | Heuristic reranking is good enough |
| RLS / database security | Local-only deployment — risk accepted |

## Context

- **Hardware**: 64GB RAM + RTX 4070 Ti SUPER 12GB VRAM
- **Chat model**: qwen3:1.7b (~1.4GB VRAM) — upgrade path: qwen3:8b or gemma3:12b
- **Embedding model**: qwen3-embedding:4b (2560-dim, truncated to 1024 for HNSW limit)
- **Season**: Set 17 Space Gods, Patch 17.1
- **Smoke test**: 60/60 PASS — 20 questions × 3 modes (v1.0)
- **DB chunks**: ~44 → 500+ target (v1.4)

## Current State

**v1.4 Smart & Polished in progress** — 2026-04-23

| Metric | Value | Notes |
|--------|-------|-------|
| Smoke test | 60/60 PASS (v1.0) | |
| Phases complete | 10/10 (v1.0–v1.3) | |
| Requirements shipped | 50/50 | v1.0 35 + v1.1 5 + v1.2 5 + v1.3 5 |
| Requirements planned | 19/19 | v1.4 KNOW + UI + SMART + RAG2 |
| DB chunks (current) | ~44 | → 500+ target in v1.4 |
| Models | qwen3:1.7b (chat) + qwen3-embedding:4b (embedding) | |
| n8n workflows | patch_monitor.json `active: true` | |
| Frontend | Patch badge + GPU status in header | |
| **NEW** Knowledge Graph | NetworkX (in progress Phase 11) | |

## Constraints

- **Privacy**: All data stays local — Ollama, Supabase, Obsidian all on-machine
- **Performance**: Must fit in 12GB VRAM — chat model capped at ~1.7B params (upgradeable to 8B)
- **TFT Policy**: No dynamic real-time overlay or opponent scouting
- **Stack**: Windows-native Ollama, Supabase local CLI, Docker Compose for app/n8n

## Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| Ollama native (not containerized) | GPU passthrough on Windows | ✅ Locked (v1.0) |
| 1024-dim embeddings (truncated from 2560) | HNSW index limit 2000 dims | ✅ Locked (v1.0) |
| Supabase local CLI | Postgres + pgvector without Docker complexity | ✅ Locked (v1.0) |
| 3-mode chat (Normal/RAG/Coach) | TFT policy compliance | ✅ Locked (v1.0) |
| SSE for streaming | Sufficient for one-way token streaming | ✅ Locked (v1.0) |
| In-memory LRU cache | MVP scale doesn't need Redis | ✅ Locked (v1.0) |
| Bearer token auth | Defense in depth | ✅ Locked (v1.0) |
| ngrok dropped | 100% local operation | ✅ Locked (v1.0) |
| Patch state in DB (not file) | Single source of truth, queryable, testable | ✅ Locked (v1.1) |
| RLS disabled | Local-only, risk accepted | ✅ Locked |
| NetworkX for knowledge graph | Fast, Python-native, easy to serialize | ✅ Planned (v1.4 Phase 11) |
| Entity JSON markers in LLM output | No prompt overhead, easy to parse | ✅ Planned (v1.4 Phase 13) |
| Graph-first query routing | Graph for direct entity lookups; RAG for complex questions | ✅ Planned (v1.4 Phase 13) |
| Tailwind-only CompCard | Replace inline styles for maintainability | ✅ Planned (v1.4 Phase 12) |
| Streaming citations via SSE | Progressive reveal improves perceived latency | ✅ Planned (v1.4 Phase 14) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

## Current Milestone: v1.4 Smart & Polished — Phases 11-14

**Started:** 2026-04-23
**Goal:** Transform from search tool → intelligent knowledge companion

---

*Last updated: 2026-04-23*
*v1.4 "Smart & Polished" — 19 requirements across Phases 11-14*
