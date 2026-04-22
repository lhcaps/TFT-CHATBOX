# Requirements: TFT Local Copilot

**Defined:** 2026-04-22
**Core Value:** A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem.

---

## v1 Requirements

### Foundation

- [ ] **FOUND-01**: Ollama runs natively on Windows, serving chat model (qwen3:8b) and embedding model (qwen3-embedding:4b) at localhost:11434
- [ ] **FOUND-02**: Supabase local CLI launches Postgres + pgvector/HNSW at port 54322 with dashboard at 54323
- [ ] **FOUND-03**: Docker Compose orchestrates backend + frontend + n8n; Ollama and Supabase run as host services
- [ ] **FOUND-04**: Health endpoint checks both Ollama and Supabase connectivity

### Backend

- [ ] **BACK-01**: FastAPI app exposes GET /health, POST /sessions, GET /sessions, POST /chat, POST /search, POST /ingest/obsidian, POST /ingest/tft-static
  *(Note: Phase 2 covers /health, /sessions, and /chat. The remaining endpoints are implemented in Phase 4.)*
- [ ] **BACK-02**: POST /chat with stream=true returns SSE with token events and done event with usage stats; stream=false returns complete JSON
- [ ] **BACK-03**: Session persistence: sessions + messages tables with proper indexes; messages persisted to DB and retrievable by session_id
- [ ] **BACK-04**: CORS configured to allow http://localhost:5173 explicitly (no wildcard)

### Frontend

- [ ] **FRONT-01**: React + Vite + Tailwind chat UI scaffolded and running at localhost:5173
- [ ] **FRONT-02**: Chat shell renders messages with user/assistant distinction, mode tabs, and input area
- [ ] **FRONT-03**: SSE streaming: tokens appear in real-time using fetch + ReadableStream pattern
- [ ] **FRONT-04**: Abort controller stops generation mid-stream
- [ ] **FRONT-05**: Mode toggle switches between Normal / RAG / Coach modes

### Database Schema

- [ ] **DB-01**: Tables: chat_sessions (uuid, title, mode, metadata, timestamps), chat_messages (bigserial, session_id, role, content, citations, usage, timestamps)
- [ ] **DB-02**: Tables: documents (uuid, source_type, source_path, source_hash, title, season, patch, locale, metadata, raw_markdown, timestamps), document_chunks (bigserial, document_id, chunk_index, heading_path, content, token_estimate, embedding vector(1024), metadata, fts tsvector, timestamps)
- [ ] **DB-03**: HNSW index on document_chunks.embedding with vector_cosine_ops
- [ ] **DB-04**: GIN index on document_chunks.fts
- [ ] **DB-05**: hybrid_search_chunks() SQL function with RRF (semantic_weight=2, full_text_weight=1)
- [ ] **DB-06**: B-tree indexes on session_id + created_at, document_id + chunk_index

### RAG Pipeline

- [ ] **RAG-01**: Obsidian vault ingest: walk .md files (skip .obsidian/), parse frontmatter, split by heading hierarchy
- [ ] **RAG-02**: Chunking: 2000 char chunks with 500 char overlap, preserving heading path as metadata
- [ ] **RAG-03**: Batch embedding via Ollama /api/embed with dimensions=1024, batch size 16
- [ ] **RAG-04**: Hash-based incremental re-ingest: source_hash on documents, DELETE before re-INSERT on changed files
- [ ] **RAG-05**: TFT static data ingestion: champions, traits, items, augments from Riot Data Dragon + CommunityDragon
- [ ] **RAG-06**: Metadata filtering: patch and season columns enable scoped retrieval
- [ ] **RAG-07**: Basic citation display: sources stored in citations JSONB field, rendered at end of response

### Prompt Modes

- [ ] **PROMPT-01**: Normal mode prompt: concise, factual, admits uncertainty
- [ ] **PROMPT-02**: RAG mode prompt: grounds answers in retrieved context, cites [doc:title > heading]
- [ ] **PROMPT-03**: Coach mode prompt: 2-3 lines of play with econ/tempo/cap/pivot framing, no dictating, no real-time scouting references

### Automation

- [ ] **AUTO-01**: n8n workflow: Schedule Trigger every 4 hours → POST /api/ingest/obsidian
- [ ] **AUTO-02**: n8n workflow: Schedule Trigger every 6 hours → check Riot versions.json → POST /api/ingest/tft-static if patch changed
- [ ] **AUTO-03**: ngrok tunnel for webhook exposure; script auto-refreshes URL on tunnel restart
- [ ] **AUTO-04**: n8n configured with GENERIC_TIMEZONE=Asia/Ho_Chi_Minh and N8N_PROXY_HOPS=1

### DevOps / Polish

- [ ] **POLY-01**: Query embedding cache: LRU with 30-minute TTL keyed by (query, mode, patch)
- [ ] **POLY-02**: Static TFT JSON on-disk cache with patch version check
- [ ] **POLY-03**: Smoke test: 20-question eval set covering comp, item, augment, pivot scenarios
- [ ] **POLY-04**: GPU memory monitoring: frontend displays current VRAM usage via Ollama /api/ps
- [ ] **POLY-05**: Windows path handling: pathlib used throughout, long paths enabled, CRLF/LF handled

---

## v2 Requirements

### RAG Enhancements
- **RAG-08**: Inline citation cards with hover/tap source snippets
- **RAG-09**: Streaming citation reveal alongside tokens
- **RAG-10**: Retrieval debug panel showing chunks, scores, sources
- **RAG-11**: Heuristic reranking: patch/season priority before cosine score
- **RAG-12**: Obsidian file watcher for real-time reactive sync

### Coach Mode Enhancements
- **PROMPT-04**: Visual line-of-play cards with icons (econ, tempo, board cap)
- **PROMPT-05**: Pivot fallback chain in every coach response
- **PROMPT-06**: In-game scenario presets (fast 8 roll, hyperoll open, 1-star holding)
- **PROMPT-07**: Coach persona customization (aggressive, safe, pivoting)

### Session Features
- **SESS-01**: Session auto-naming from first message
- **SESS-02**: Session search by keyword
- **SESS-03**: Session export as Markdown to Obsidian
- **SESS-04**: Cross-session memory from past conversations

### Model Upgrades
- **MODEL-01**: gemma3:12b for Coach mode, qwen3:8b for Normal/RAG
- **MODEL-02**: Query embedding cache (30-min TTL)

### Eval / Observability
- **EVAL-01**: Smoke test suite with scoring
- **EVAL-02**: Retrieval quality metrics (recall@K)
- **EVAL-03**: Structured logging for every request

---

## v1.2 Requirements (MetaTFT Intelligence)

### MetaTFT Intelligence

- [x] **META-01**: `POST /api/ingest/metatft` — httpx scrape of `https://www.metatft.com/comps`, regex JSON extraction, Markdown transform, ingest into chunks table with `source='metatft'`
- [x] **META-02**: MetaTFT data transformer — comp name, tier, top4 rate, carry, items → Vietnamese Markdown
- [x] **META-03**: Full Space Gods data ingest — patch 17.1 full content + set overview from Riot (champions, traits, items, augments, artifacts)
- [x] **META-04**: n8n daily trigger at 12:00 noon calling `POST /api/ingest/metatft`
- [x] **META-05**: Frontend `CompCard` component — tier badges, champion names, item color coding from Markdown

### Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| META-01 | Phase 9 | Complete ✅ |
| META-02 | Phase 9 | Complete ✅ |
| META-03 | Phase 9 | Complete ✅ |
| META-04 | Phase 9 | Complete ✅ |
| META-05 | Phase 9 | Complete ✅ |

---

## v1.3 Requirements (Hardening & Polish)

### Hardening & Polish

- [x] **HARD-01**: Session switch loading state — spinner overlay on ChatShell when `messagesLoading === true`
- [x] **HARD-02**: Frontend request timeout — 60s `AbortSignal.timeout(60_000)` on `/api/chat` fetch
- [x] **HARD-03**: Pydantic validation bounds — `top_k` Field(ge=1, le=50), session_id regex validator
- [x] **HARD-04**: CompCard component — Phase 9 META-05 gap, styled tier/carry/item cards in MessageList
- [x] **HARD-05**: Toast notification system — success/error/info toasts with auto-dismiss in App.tsx

### Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| HARD-01 | Phase 10 | Complete ✅ |
| HARD-02 | Phase 10 | Complete ✅ |
| HARD-03 | Phase 10 | Complete ✅ |
| HARD-04 | Phase 10 | Complete ✅ |
| HARD-05 | Phase 10 | Complete ✅ |

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time opponent scouting / board scanning | Violates Riot TFT policy |
| In-game overlay or HUD | Violates TFT policy; dictates decisions |
| Automated "best action" button or macro | Removes player agency |
| Cloud API dependencies | Must remain fully local |
| Auth / user management | Single local user, no multi-user need |
| Non-Windows targets | MVP is Windows-only |
| WebSocket instead of SSE | SSE is sufficient for streaming |
| Redis or distributed cache | In-memory LRU sufficient for MVP |
| Cross-encoder reranking | Heuristic reranking is good enough for MVP |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Pending |
| FOUND-03 | Phase 1 | Pending |
| FOUND-04 | Phase 1 | Pending |
| BACK-01 | Phase 2 | Pending |
| BACK-02 | Phase 2 | Pending |
| BACK-03 | Phase 2 | Pending |
| BACK-04 | Phase 2 | Pending |
| FRONT-01 | Phase 3 | Pending |
| FRONT-02 | Phase 3 | Pending |
| FRONT-03 | Phase 3 | Pending |
| FRONT-04 | Phase 3 | Pending |
| FRONT-05 | Phase 3 | Pending |
| DB-01 | Phase 1 | Pending |
| DB-02 | Phase 1 | Pending |
| DB-03 | Phase 1 | Pending |
| DB-04 | Phase 1 | Pending |
| DB-05 | Phase 1 | Pending |
| DB-06 | Phase 1 | Pending |
| RAG-01 | Phase 4 | Pending |
| RAG-02 | Phase 4 | Pending |
| RAG-03 | Phase 4 | Pending |
| RAG-04 | Phase 4 | Pending |
| RAG-05 | Phase 4 | Pending |
| RAG-06 | Phase 4 | Pending |
| RAG-07 | Phase 4 | Pending |
| PROMPT-01 | Phase 4 | Pending |
| PROMPT-02 | Phase 4 | Pending |
| PROMPT-03 | Phase 4 | Pending |
| AUTO-01 | Phase 6 | Pending |
| AUTO-02 | Phase 6 | Pending |
| AUTO-03 | Phase 6 | Pending |
| AUTO-04 | Phase 6 | Pending |
| POLY-01 | Phase 7 | Pending |
| POLY-02 | Phase 5 | Pending |
| POLY-03 | Phase 7 | Pending |
| POLY-04 | Phase 7 | Pending |
| POLY-05 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 35 total
- Mapped to phases: 35
- Unmapped: 0 ✓
- v1.2 (META-01..05): 5/5 complete ✅
- v1.3 (HARD-01..05): 5/5 complete ✅

---

*Requirements defined: 2026-04-22*
*Last updated: 2026-04-23 after Phase 9 + Phase 10 completion*
