# TFT Local Copilot

## What This Is

A local-first AI copilot for Teamfight Tactics (TFT Set 17 Space Gods, Patch 17.1) that runs entirely on the user's machine — no cloud APIs, no external dependencies. Three chat modes: **Normal** (free chat), **RAG** (retrieve from notes + patch data), and **Coach** (2-3 lines of play with trade-off analysis). Stack: React chat UI + FastAPI backend + Ollama local LLM + Supabase pgvector RAG + Obsidian knowledge source.

## Core Value

A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem.

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

### Active

- [ ] Patch state in DB + auto-ingest pipeline (PATCH-01, PATCH-02)
- [ ] Auto-scrape patch notes on new patch (PATCH-03)
- [ ] n8n workflow activation + monitoring (PATCH-04)
- [ ] Frontend patch version + staleness display (PATCH-05)
- [ ] Session auto-naming and search (SESS-01, SESS-02)
- [ ] Session export to Obsidian Markdown (SESS-03)
- [ ] Inline citation cards with hover source snippets (RAG-08)
- [ ] Streaming citation reveal alongside tokens (RAG-09)
- [ ] Retrieval debug panel showing chunks and scores (RAG-10)
- [ ] Coach visual line-of-play cards (PROMPT-04)
- [ ] Coach persona customization (PROMPT-07)
- [ ] Cross-session memory (SESS-04)
- [ ] Model upgrade: gemma3:12b for Coach mode (MODEL-01)

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
| Cross-encoder reranking | Heuristic reranking is good enough for MVP |
| RLS / database security | Local-only deployment — risk accepted |

## Context

- **Hardware**: 64GB RAM + RTX 4070 Ti SUPER 12GB VRAM
- **Chat model**: qwen3:1.7b (~1.4GB VRAM)
- **Embedding model**: qwen3-embedding:4b (2560-dim, truncated to 1024 for HNSW limit)
- **Season**: Set 17 Space Gods, Patch 17.1
- **Smoke test**: 60/60 PASS — 20 questions × 3 modes
- **Design source**: deep-research-report.md

## Current State

**v1.1 TFT Meta Mastery** — in progress

| Metric | Value |
|--------|-------|
| Smoke test | 60/60 PASS (v1.0) |
| Phases complete | 7/7 (v1.0) |
| Requirements shipped | 35/35 (v1.0) |
| DB chunks | 32 (TFT patch 17.1) |
| Models | qwen3:1.7b (chat) + qwen3-embedding:4b (embedding) |
| n8n workflows | patch_monitor.json exists but `active: false` |

## Constraints

- **Privacy**: All data stays local — Ollama, Supabase, Obsidian all on-machine
- **Performance**: Must fit in 12GB VRAM — chat model capped at ~1.7B params
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
| Patch state in DB (not file) | More reliable, queryable, testable | 🔄 v1.1 |
| RLS disabled | Local-only, risk accepted | ✅ Locked |

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

## Current Milestone: v1.1 TFT Meta Mastery

**Goal:** Automated TFT meta intelligence — backend tracks patch state in DB, n8n monitors Riot for new patches, auto-ingests patch notes + static data when available.

**Target features:**
- Patch state persisted in DB (not just file)
- Auto-scrape & ingest patch notes on new patch detection
- n8n workflow activates and monitors patch changes
- Frontend displays patch version + staleness status

---
*Last updated: 2026-04-22*
