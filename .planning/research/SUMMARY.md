# TFT Local Copilot — Research Summary

**Project:** Local AI chatbot for Teamfight Tactics (Set 17 Space Gods)
**Hardware:** 64GB RAM + RTX 4070 Ti SUPER 16GB VRAM
**Researched:** 2026-04-22

---

## Executive Summary

TFT Local Copilot is a **fully offline AI coaching tool** for Teamfight Tactics players. It combines a React chat UI with a FastAPI backend powered by Ollama (local LLM inference), Supabase (Postgres + pgvector for hybrid search), and Obsidian as a knowledge base. Three modes serve distinct use cases: **Normal** (free-form chat), **RAG** (grounded answers from personal notes + patch data), and **Coach** (2-3 lines of play with trade-off analysis). Everything runs locally — no cloud APIs, no external data collection, full privacy.

The key insight: the app's value comes from **grounding answers in accurate game data** (champion stats, trait synergies, item recipes) and **personal context** (player notes, meta observations). Without RAG, it's just a generic chatbot. The stack is optimized for a single Windows machine with discrete GPU — native Ollama for GPU access, Supabase CLI for zero-friction pgvector setup, Docker Compose for app services.

**TFT Policy is non-negotiable.** This app must never provide real-time overlays, opponent scouting, or "do this now" commands. Coach mode always suggests options with trade-offs, never dictates decisions.

---

## Key Stack Decisions

| Decision | Rationale | Confidence |
|----------|-----------|------------|
| **Ollama native (not Docker)** | GPU passthrough friction on Windows/WSL2; native directly accesses RTX 4070 Ti | HIGH |
| **qwen3:8b for chat** | Fits in 5.2GB VRAM, good Vietnamese support, 4K-8K context | HIGH |
| **qwen3-embedding:4b** | 1024-dim output stays under HNSW 2000-dim limit | HIGH |
| **FastAPI + SSE streaming** | Native async, StreamingResponse for token-by-token output | HIGH |
| **httpx over requests** | Truly async, better connection pooling for concurrent Ollama calls | HIGH |
| **asyncpg over psycopg2** | Non-blocking Postgres access (psycopg2 blocks event loop) | HIGH |
| **Supabase local CLI** | One-command Postgres + pgvector + dashboard, no Docker complexity | HIGH |
| **HNSW index** | Higher recall than IVFFlat for <10M vectors; consistent query latency | HIGH |
| **1024-dim embeddings** | Below HNSW 2000-dim hard limit; configurable in Ollama API | HIGH |
| **React + Vite + Tailwind 4** | Current 2026 standard: fast HMR, minimal config, dark mode via `dark:` | HIGH |

---

## Core Features

### Table Stakes (MVP — ship these or the product feels broken)

- **Streaming responses (SSE)** — Token-by-token output; 3-8s local LLM latency makes non-streaming feel frozen
- **Mode switching (Normal / RAG / Coach)** — Three distinct use cases need explicit UI toggling
- **Abort / stop generation** — Users must kill irrelevant long responses without page refresh
- **Chat history list + message persistence** — Sessions survive app restart
- **Basic citation display (end-of-response)** — Shows which documents grounded the answer
- **Obsidian vault ingest** — On-demand file-based ingestion with heading + fixed-size chunking
- **Hybrid search (HNSW + FTS + RRF)** — Pure vector misses exact TFT terms; pure FTS misses semantic intent
- **Metadata filtering (patch, season)** — Stale patch data actively misleads; users must scope to current patch
- **TFT static data ingestion** — Champions, traits, items, augments from Riot Data Dragon + CommunityDragon
- **Coach line-of-play cards (2-3 options)** — "Just tell me what to do" is the #1 failure mode; options + trade-offs comply with TFT policy
- **Trade-off framing (econ, tempo, board cap, pivot)** — Professional depth, explainable reasoning
- **Healthcheck (app + DB + Ollama)** — Debugging startup failures without health checks is guesswork
- **Model keep-alive (15m)** — Cold model load takes 5-15s; pre-loading eliminates first-request penalty

### Differentiators (v2+ — valued but not expected)

- **Inline citation cards** — Per-sentence hover/tap for source snippets (hard: requires token-level attribution)
- **Streaming citation reveal** — Citations appear alongside tokens, not just at end
- **Retrieval debug panel** — Show which chunks retrieved, scores, sources
- **Coach pivot fallback chain** — "If X happens, pivot to Y" addresses TFT's dynamic nature
- **In-game scenario presets** — Pre-built context: "fast 8 roll", "hyperoll open", "1-star board holding"
- **n8n scheduled Obsidian sync** — Automated 4-hour ingest without manual trigger
- **Patch change detection** — Riot releases every 2 weeks; auto-refresh static data
- **Session auto-naming** — Title sessions by content, not "Session #42"
- **Smoke test suite (20-question eval)** — Core RAG + Coach responses don't regress

---

## Architecture Highlights

### Components & Boundaries

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER MACHINE                                  │
│                                                                      │
│  ┌──────────────┐              ┌────────────────────────┐           │
│  │   Ollama     │              │   Supabase Local CLI   │           │
│  │  (Native)    │              │  ┌──────────────────┐  │           │
│  │  :11434      │              │  │ PostgreSQL +     │  │           │
│  │  GPU: RTX    │              │  │ pgvector/HNSW   │  │           │
│  │  4070 Ti     │              │  │  :54322 (DB)    │  │           │
│  │  SUPER 16GB  │              │  │  :54323 (Studio)│  │           │
│  └──────┬───────┘              └──┴─────────┬────────┘           │
│         │ host.docker.internal              │                       │
│         │ localhost                          │                       │
│         ▼                                   ▼                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    DOCKER SERVICES                             │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐                 │   │
│  │  │ Backend  │    │ Frontend │    │   n8n    │                 │   │
│  │  │ FastAPI  │    │React/Vite│    │Automate  │                 │   │
│  │  │  :8000   │    │  :5173   │    │  :5678   │                 │   │
│  │  └──────────┘    └──────────┘    └──────────┘                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                        │                   │
│         │ http://localhost:8000                  │                   │
│         │ http://localhost:5173                  │                   │
│         ▼                                        ▼                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      BROWSER                                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      FILE SYSTEM                              │   │
│  │  ┌─────────────────────┐    ┌─────────────────────────────┐  │   │
│  │  │   Obsidian Vault   │    │      TFT Static Data         │  │   │
│  │  │  (Markdown notes)  │    │  (JSON: champions, items...) │  │   │
│  │  └─────────────────────┘    └─────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Chat Request → Ollama → SSE → Frontend**
   - User message → FastAPI `/api/chat/stream` → Ollama `/api/chat` (streaming)
   - Backend transforms Ollama NDJSON to SSE format: `event: token\ndata: {...}\n\n`
   - Frontend consumes via `fetch` + `ReadableStream.getReader()` (NOT EventSource — requires POST with body)

2. **RAG Query → Embed → Search → Inject → Respond**
   - Query embedding via Ollama `/api/embed`
   - Hybrid search: `hybrid_search_chunks()` with RRF (Reciprocal Rank Fusion)
   - Top 6-8 chunks assembled into context → injected into chat prompt → Ollama responds

3. **Ingestion → Chunk → Embed → Store**
   - Markdown files split by headings, then fixed-size chunks (2000 chars, 25% overlap)
   - Batch embed 16 chunks at a time via Ollama `/api/embed`
   - Upsert to Supabase with hash-based deduplication

### Key API Routes

| Route | Purpose | Calls |
|-------|---------|-------|
| `GET /health` | System health | Ollama `/api/tags`, Supabase |
| `POST /api/sessions` | Create chat session | Supabase |
| `GET /api/sessions` | List sessions | Supabase |
| `POST /api/chat/stream` | Streaming chat | Ollama + optional retrieval |
| `POST /api/search` | Debug retrieval | Hybrid search SQL |
| `POST /api/ingest/*` | Trigger ingestion | Ollama embed + Supabase |

---

## Critical Pitfalls to Avoid

### Ollama / GPU

1. **GPU not used (CPU fallback)** — `ollama ps` shows `Processor: CPU` → 10-20x slower
   - Fix: Verify CUDA drivers, `CUDA_VISIBLE_DEVICES=0`, Ollama 0.5+ has better GPU detection

2. **Context overflow / token limit** — Truncated responses, `eval_count` near `num_ctx`
   - Fix: Set `num_ctx: 8192` explicitly; implement sliding window for long conversations

3. **Model not loaded (keep_alive too short)** — First request takes 30-60s
   - Fix: Set `keep_alive: "15m"` in streaming request

4. **Docker can't reach native Ollama** — Connection refused to `localhost:11434` from container
   - Fix: Use `host.docker.internal:11434` in Docker Compose, not `localhost`

5. **Embedding dimension mismatch** — pgvector throws "dimension mismatch" error
   - Fix: Always specify `dimensions: 1024` in Ollama `/api/embed` request

### pgvector / Database

6. **HNSW index dimension exceeded** — 2000-dim hard limit
   - Fix: Use 1024-dim embeddings; never exceed 2000

7. **Duplicate chunks on re-ingest** — Same document appears multiple times
   - Fix: `DELETE FROM document_chunks WHERE document_id = $1` before re-inserting; hash-based skip

### React / Streaming

8. **SSE stream truncation** — Partial tokens at end of stream
   - Fix: Accumulate in buffer, split on `\n\n`; handle incomplete lines

9. **Abort doesn't cancel properly** — Stream keeps yielding after stop
   - Fix: Call `reader.cancel()` + `reader.releaseLock()` on abort; clean up state

10. **CORS preflight failure** — `No 'Access-Control-Allow-Origin' header`
    - Fix: FastAPI explicitly allows `http://localhost:5173`; include headers/methods in config

### Windows

11. **Path separators** — `FileNotFoundError` on Windows, works on Linux
    - Fix: Use `pathlib.Path` for all path operations; never hardcode `/` or `\`

12. **Line endings (CRLF vs LF)** — "bad interpreter" on Windows
    - Fix: `.gitattributes` with `*.py text eol=lf`; `core.autocrlf input`

---

## TFT Policy Boundaries

**These features must NEVER be built — they violate Riot Games TFT policy:**

| Anti-Feature | Why Prohibited | What To Build Instead |
|--------------|----------------|----------------------|
| **Real-time opponent scouting / board scanning** | Automatically gathering opponent data = unfair advantage | Static meta analysis, general line-of-play coaching |
| **In-game overlay that dictates decisions** | Tells player "roll now", "sell X" during match | Pre-game coaching, post-game analysis |
| **Matchmaking/ranking integration with live counter-picks** | Live counter-comps based on rank = dynamic advantage | Historical matchup analysis from own past games |
| **Real-time LP/rank tracking overlay** | Live LP gains/losses, decisions based on standing | Pre-session goal setting, end-of-session review |
| **External data collection or cloud sync** | Violates local-only privacy promise + Riot data policies | All data stays in Supabase local |
| **Automated "best action" button/macro** | Removes player agency | Coaching suggestions with human decision-making |
| **Dictating augments/items in real-time** | "Pick Prismatic Ticket" during match = decision dictation | Pre-match augment strategy, general itemization principles |

**Coach mode must always:**
- Suggest 2-3 lines of play (never single mandatory action)
- Include trade-off framing: econ loss, tempo risk, board cap, pivot fallback
- Frame as "consider" not "must"

---

## Suggested Build Phases

### Phase 1: Environment Setup (Days 1-2)
- Install Ollama, pull models (`qwen3:8b`, `qwen3-embedding:4b`)
- Verify GPU: `ollama ps` shows `size_vram > 0`
- Supabase local: `npx supabase init && supabase start`
- Create database schema (4 tables: sessions, messages, documents, chunks)
- Docker Compose scaffold (backend, frontend, n8n)
- **Pitfalls to avoid:** GPU detection, path separators, CRLF line endings

### Phase 2: Backend Core (Days 2-3)
- FastAPI skeleton with routes: `/health`, `/api/sessions`, `/api/chat`
- Ollama non-streaming chat working
- Session persistence: create, list, retrieve
- CORS configuration for `localhost:5173`
- **Pitfalls to avoid:** CORS preflight, Ollama unreachable from Docker (`host.docker.internal`)

### Phase 3: Frontend Shell + Streaming (Day 3)
- Vite + React scaffold with Tailwind 4
- Chat UI: messages display, input sends
- SSE streaming: tokens appear in real-time
- Abort controller: stop generation works
- **Pitfalls to avoid:** SSE buffer accumulation, ReadableStream handling, abort cleanup

### Phase 4: RAG Integration (Days 4-5)
- Hybrid search SQL function: `hybrid_search_chunks()` with RRF
- Obsidian ingest: Markdown → chunks → embeddings → Supabase
- RAG mode in chat: context injected into prompt
- Coach mode: multi-line-of-play prompts
- Citation tracking: sources stored with messages
- **Pitfalls to avoid:** Wrong embedding dimensions (1024), duplicate chunks (DELETE before INSERT), heading-aware chunking edge cases

### Phase 5: Coach Mode Polish (Days 5-6)
- Line-of-play cards as structured JSON output
- Trade-off dimensions: econ, tempo, board cap, pivot
- Coach persona customization
- **Pitfalls to avoid:** TFT policy violations — no dictation, always suggest options

### Phase 6: Automation + Polish (Days 6-7)
- n8n scheduled Obsidian ingest (4-hour sync)
- Patch change detection + auto-refresh
- Data versioning / patch rollback
- Query embedding cache (30-min TTL)
- **Pitfalls to avoid:** n8n workflow not activated, ngrok URL changes, timezone misconfiguration

### Phase 7: Production Quality (Post-MVP)
- Smoke test suite (20-question eval set)
- Retrieval quality metrics (recall@K)
- Logging + observability
- Session auto-naming
- Session export (Markdown to Obsidian)

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Frontend Stack | HIGH | React/Vite/Tailwind ecosystem well-established |
| Backend Stack | HIGH | FastAPI proven for LLM streaming apps |
| Ollama Integration | HIGH | Direct from Ollama official docs |
| SSE Architecture | HIGH | Based on FastAPI official examples |
| pgvector/HNSW | HIGH | Based on Supabase official documentation |
| Docker Compose | MEDIUM | Pattern verified, Windows-specific nuances may vary |
| Windows Toolchain | MEDIUM | General guidance, no major ecosystem changes |
| TFT Policy | HIGH | Based on Riot public policy documentation |

### Gaps to Address During Planning

1. **Chunking quality** — Heading + fixed-size is sufficient for MVP, but real retrieval quality only measurable after loading personal notes
2. **Coach prompt tuning** — Line-of-play framing requires iteration against actual model outputs
3. **RAG evaluation** — Recall@K metrics needed to validate hybrid search effectiveness
4. **Vietnamese localization** — qwen3's Vietnamese capability needs verification for technical TFT terminology

---

## Sources

| Source | Confidence | Used For |
|--------|------------|----------|
| deep-research-report.md | HIGH | Architecture, stack, schema, prompts, automation |
| Ollama API docs | HIGH | Streaming, embedding, model configuration |
| FastAPI SSE docs | HIGH | Streaming response patterns |
| Supabase pgvector docs | HIGH | HNSW configuration, hybrid search |
| Riot Games TFT policy | HIGH | Policy compliance requirements |
| pgvector performance (Crunchy Data) | HIGH | HNSW tuning parameters |
| Docker + Ollama GPU setup | MEDIUM | Windows-specific networking patterns |
| Tailwind + Vite setup (DEV) | MEDIUM | Current 2026 frontend tooling |

---

*Synthesized: 2026-04-22*
