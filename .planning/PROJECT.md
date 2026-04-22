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

## Context

- **Hardware**: 64GB RAM + RTX 4070 Ti SUPER 12GB VRAM (adjusted from 16GB)
- **Chat model**: qwen3:1.7b (~1.4GB VRAM) — switched from qwen3:8b for 12GB VRAM compatibility
- **Embedding model**: qwen3-embedding:4b (creates 2560-dim, truncated to 1024 for DB HNSW limit)
- **Season**: Set 17 Space Gods, Patch 17.1
- **Smoke test**: 60/60 PASS — 20 questions across 4 categories × 3 modes
- **Design source**: deep-research-report.md

## Current State

**v1.0 MVP shipped** — 2026-04-22

| Metric | Value |
|--------|-------|
| Smoke test | 60/60 PASS |
| Phases complete | 7/7 |
| Requirements shipped | 35/35 |
| DB chunks | 32 (TFT patch 17.1) |
| Models | qwen3:1.7b (chat) + qwen3-embedding:4b (embedding) |

## Constraints

- **Privacy**: All data stays local — Ollama, Supabase, Obsidian all on-machine
- **Performance**: Must fit in 12GB VRAM — chat model capped at ~1.7B params
- **TFT Policy**: No dynamic real-time overlay or opponent scouting
- **Stack**: Windows-native Ollama, Supabase local CLI, Docker Compose for app/n8n

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Ollama native (not containerized) | GPU passthrough in Docker on Windows | ✅ Shipped |
| 1024-dim embeddings (truncated from 2560) | HNSW index limit 2000 dims | ✅ Shipped — consider 1024-dim model |
| Supabase local CLI | Postgres + pgvector + dashboard without Docker complexity | ✅ Shipped |
| 3-mode chat (Normal/RAG/Coach) | TFT policy compliance | ✅ Shipped |
| SSE for streaming | Sufficient for one-way token streaming | ✅ Shipped |
| In-memory LRU cache | MVP scale | ✅ Shipped |
| Bearer token auth | Defense in depth | ✅ Shipped |
| qwen3:1.7b for 12GB VRAM | Quality vs. VRAM tradeoff | ✅ Shipped — shorter responses than qwen3:8b |
| ngrok dropped | 100% local operation | ✅ Shipped |

---

*Last updated: 2026-04-22 after v1.0 MVP milestone completion*
