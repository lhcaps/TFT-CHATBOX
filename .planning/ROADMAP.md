# ROADMAP: TFT Local Copilot

**Project:** TFT Local Copilot
**Created:** 2026-04-22
**Granularity:** standard
**Parallelization:** enabled (yolo mode)

---

## Phases

- [x] **Phase 1: Environment Setup** - Ollama + Supabase + Database Schema
- [ ] **Phase 2: Backend Core** - FastAPI skeleton, session API, non-streaming chat
- [ ] **Phase 3: Frontend Chat** - React + Vite + SSE streaming + mode toggle
- [ ] **Phase 4: RAG Foundation** - Obsidian ingest, hybrid search, Coach prompts
- [ ] **Phase 5: TFT Static Data** - Riot + CommunityDragon ingestion, metadata filtering
- [ ] **Phase 6: Automation** - n8n workflows, ngrok, patch monitoring
- [ ] **Phase 7: Polish & Smoke Test** - Caching, GPU monitoring, 20-question eval

---

## Phase Details

### Phase 1: Environment Setup

**Goal:** Development environment is fully operational with Ollama, Supabase, database schema, and Docker Compose configured.

**Depends on:** Nothing (foundation)

**Requirements:** FOUND-01, FOUND-02, FOUND-03, FOUND-04, DB-01, DB-02, DB-03, DB-04, DB-05, DB-06, POLY-05

**Success Criteria** (what must be TRUE):
1. `ollama ps` shows qwen3:8b and qwen3-embedding:4b loaded with GPU usage (VRAM > 0)
2. `npx supabase status` shows Postgres healthy at port 54322 and Studio at 54323
3. Database schema migrations run successfully — all 4 tables exist with correct columns
4. HNSW and GIN indexes created without errors; hybrid_search_chunks function callable
5. `docker compose ps` shows backend and n8n containers running
6. All Python scripts use `pathlib` and paths work on Windows

**Plans:** 5 plans

Plans:
- [ ] 01-01-PLAN.md — Ollama + Supabase Installation
- [ ] 01-02-PLAN.md — Database Schema Migration
- [ ] 01-03-PLAN.md — Docker Compose Setup
- [ ] 01-04-PLAN.md — Healthcheck Endpoint
- [ ] 01-05-PLAN.md — Directory Structure + Windows Config

---

### Phase 2: Backend Core

**Goal:** FastAPI backend exposes all required endpoints with session persistence and Ollama integration working.

**Depends on:** Phase 1

**Requirements:** BACK-01, BACK-02, BACK-03, BACK-04

**Success Criteria** (what must be TRUE):
1. GET /health returns {"ollama": "healthy", "database": "healthy"} when services are running
2. POST /api/sessions creates a new session and returns UUID; GET /api/sessions lists sessions
3. POST /api/chat with non-streaming mode returns a complete response from Ollama
4. CORS allows requests from http://localhost:5173; requests from other origins are blocked
5. Chat messages are persisted to database and retrievable by session_id

**Plans:** 4 plans

Plans:
- [ ] 02-01-PLAN.md — Repository Layer (SessionRepository + MessageRepository + CHAT_HISTORY_WINDOW config)
- [ ] 02-02-PLAN.md — Sessions API (Replace in-memory with DB-backed SessionRepository)
- [ ] 02-03-PLAN.md — Chat Endpoint (Structured SSE + history windowing + non-streaming)
- [ ] 02-04-PLAN.md — End-to-End Verification (Health, sessions, chat, CORS)

**UI hint:** yes

---

### Phase 3: Frontend Chat

**Goal:** Users can chat with streaming responses and switch between Normal/RAG/Coach modes.

**Depends on:** Phase 2

**Requirements:** FRONT-01, FRONT-02, FRONT-03, FRONT-04, FRONT-05

**Success Criteria** (what must be TRUE):
1. React app loads at localhost:5173 with dark mode theme matching Tailwind
2. User can type a message and see tokens appear in real-time as the model generates
3. Clicking "Stop" immediately halts generation and preserves any partial response
4. Clicking mode tabs (Normal/RAG/Coach) switches the active mode indicator
5. Previous messages persist on page refresh (localStorage or API-backed)

**Plans:** TBD

**UI hint:** yes

---

### Phase 4: RAG Foundation

**Goal:** System retrieves relevant context from Obsidian vault and provides grounded, cited responses in RAG and Coach modes.

**Depends on:** Phase 3

**Requirements:** RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06, RAG-07, PROMPT-01, PROMPT-02, PROMPT-03

**Success Criteria** (what must be TRUE):
1. POST /api/ingest/obsidian processes a test vault and returns chunk count without errors
2. POST /api/search returns relevant chunks with scores for a TFT query
3. RAG mode response includes citations formatted as [doc:title > heading]
4. Coach mode response includes 2-3 lines of play with econ/tempo/cap framing
5. Re-ingesting changed files updates chunks without duplicating (hash-based)
6. Batch embedding processes 16 chunks per request without VRAM overflow

**Plans:** TBD

---

### Phase 5: TFT Static Data

**Goal:** Champions, traits, items, and augments are ingested from Riot Data Dragon and CommunityDragon with season/patch metadata.

**Depends on:** Phase 4

**Requirements:** RAG-05, RAG-06, POLY-02

**Success Criteria** (what must be TRUE):
1. /api/ingest/tft-static successfully downloads and processes at least one champion JSON
2. Chunks include season and patch metadata; queries can filter by patch version
3. On-disk TFT JSON cache exists and avoids re-downloading unchanged patch data
4. Metadata filtering enables scoped retrieval (e.g., "show only 17.1 augments")

**Plans:** TBD

---

### Phase 6: Automation

**Goal:** n8n workflows handle scheduled ingest and patch monitoring; ngrok exposes webhooks reliably.

**Depends on:** Phase 5

**Requirements:** AUTO-01, AUTO-02, AUTO-03, AUTO-04

**Success Criteria** (what must be TRUE):
1. n8n workflow for Obsidian ingest triggers every 4 hours when active
2. n8n workflow checks Riot versions.json every 6 hours and triggers ingest on patch change
3. ngrok tunnel starts and refreshes WEBHOOK_URL in n8n without manual intervention
4. All workflows run in Asia/Ho_Chi_Minh timezone as configured

**Plans:** TBD

---

### Phase 7: Polish & Smoke Test

**Goal:** System is production-ready with caching, GPU monitoring, and passing smoke test evaluation.

**Depends on:** Phase 6

**Requirements:** POLY-01, POLY-03, POLY-04

**Success Criteria** (what must be TRUE):
1. Query embedding cache returns cached results within 50ms for repeated queries
2. Frontend displays current VRAM usage from Ollama /api/ps endpoint
3. All 20 smoke test questions receive coherent, relevant answers without errors
4. GPU memory stays under 16GB during normal operation (verified via monitoring)

**Plans:** TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Environment Setup | 5/5 | Complete | 2026-04-22 |
| 2. Backend Core | 0/N | Not started | - |
| 3. Frontend Chat | 0/N | Not started | - |
| 4. RAG Foundation | 0/N | Not started | - |
| 5. TFT Static Data | 0/N | Not started | - |
| 6. Automation | 0/N | Not started | - |
| 7. Polish & Smoke Test | 0/N | Not started | - |

---

## Coverage Summary

| Category | Requirements | Phase |
|----------|-------------|-------|
| Foundation | FOUND-01, FOUND-02, FOUND-03, FOUND-04 | Phase 1 |
| Database Schema | DB-01, DB-02, DB-03, DB-04, DB-05, DB-06 | Phase 1 |
| Backend | BACK-01, BACK-02, BACK-03, BACK-04 | Phase 2 |
| Frontend | FRONT-01, FRONT-02, FRONT-03, FRONT-04, FRONT-05 | Phase 3 |
| RAG Pipeline | RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06, RAG-07 | Phase 4 |
| Prompt Modes | PROMPT-01, PROMPT-02, PROMPT-03 | Phase 4 |
| TFT Static Data | RAG-05, RAG-06, POLY-02 | Phase 5 |
| Automation | AUTO-01, AUTO-02, AUTO-03, AUTO-04 | Phase 6 |
| Polish | POLY-01, POLY-03, POLY-04, POLY-05 | Phase 1, 7 |

**Total:** 35/35 requirements mapped ✓

---

## TFT Policy Compliance Notes

All phases must comply with Riot TFT policy:
- **No real-time data:** Never build overlay, screen capture, or opponent scouting features
- **No game state reading:** Coach mode suggestions based on user's stated context only
- **Suggest, don't dictate:** Coach responses frame recommendations as options with trade-offs
- **Local-only:** All data stays on user's machine — no external API calls except Riot Data Dragon (static)
- **Unofficial tool:** Clearly disclaim no affiliation with Riot Games

---

*Last updated: 2026-04-22*
*Completed: 2026-04-22*
