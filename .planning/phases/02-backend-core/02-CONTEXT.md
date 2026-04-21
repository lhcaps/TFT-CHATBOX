# Phase 2: Backend Core - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the FastAPI backend into a fully functional API: session/message persistence to Postgres, chat with full conversation history, streaming SSE with structured events, and non-streaming fallback. The scaffold from Phase 1 (placeholder files) is wired together into a working system.

**Scope:** POST /api/chat, GET/POST /api/sessions, DB-backed session/message CRUD, streaming + non-streaming modes, history windowing.
**Out of scope:** RAG retrieval, Coach prompting, ingest pipelines (Phase 4), n8n automation (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Message history (D-01 to D-03)
- **D-01:** Use a **rolling window of last N messages** + system prompt per request
- **D-02:** System prompt always included (not counted in the window)
- **D-03:** Default window size: **10 messages**, configurable via `CHAT_HISTORY_WINDOW` env var

### SSE event format (D-04 to D-08)
- **D-04:** Token events: `data: {"token": "word"}\n\n` — structured JSON, not raw text
- **D-05:** Done event: `data: {"done": true, "done_reason": "stop"|"length"|"tool_call"}\n\n`
- **D-06:** Usage event: `data: {"usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}}\n\n`
- **D-07:** Usage data comes from Ollama's response (or estimated from character count if not available)
- **D-08:** Citation events (Phase 4 scope): `data: {"citation": {"doc": "...", "heading": "...", "score": 0.9}}\n\n`

### Non-streaming chat (D-09 to D-10)
- **D-09:** Single endpoint: `POST /api/chat` with `stream: bool` parameter (default `True`)
- **D-10:** Non-streaming returns structured JSON:
  ```json
  {
    "text": "response text",
    "usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N},
    "done_reason": "stop",
    "citations": []
  }
  ```

### Database access layer (D-11 to D-12)
- **D-11:** Repository pattern: `app/repositories/session.py` + `app/repositories/message.py`
- **D-12:** Raw `asyncpg` — no ORM or SQL model library, full SQL control

### Session/message persistence (D-13 to D-14)
- **D-13:** Sessions stored in `chat_sessions` table (UUID, title, mode, metadata, timestamps)
- **D-14:** Messages stored in `chat_messages` table (bigserial PK, session_id FK, role, content, citations JSONB, usage JSONB, timestamps)

### Claude's Discretion
- Exact `ef_construction` and `m` values for HNSW index (Phase 1 defaults are fine)
- `ollama_keep_alive` value during chat sessions (keep at 15m from Phase 1)
- How to handle the initial system message per session mode (create once at session start)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project context
- `.planning/PROJECT.md` — Vision, stack, constraints, TFT policy compliance
- `.planning/REQUIREMENTS.md` — BACK-01 to BACK-04, DB-01 to DB-06
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, dependencies
- `.planning/STATE.md` — Accumulated context, locked decisions from Phase 1

### Prior phase context
- `.planning/phases/01-environment-setup/01-CONTEXT.md` — All Phase 1 decisions (Ollama, Supabase, DB schema, Docker, ports)

### Existing code (read before implementing)
- `apps/backend/app/main.py` — FastAPI app with CORS middleware already configured
- `apps/backend/app/config.py` — Settings class with all env vars (needs CHAT_HISTORY_WINDOW added)
- `apps/backend/app/db.py` — asyncpg pool getter (ready to use in repositories)
- `apps/backend/app/models.py` — Pydantic models (needs ChatRequest updated, new streaming event models)
- `apps/backend/app/routes/sessions.py` — Currently in-memory (replace with DB-backed)
- `apps/backend/app/routes/chat.py` — Basic streaming (needs history, mode, structured events)
- `apps/backend/app/prompts.py` — System prompts for Normal/RAG/Coach (ready to use)

### Database schema
- `supabase/migrations/0001_initial_schema.sql` — Full table definitions with columns, indexes, and hybrid_search_chunks function

### Research findings
- `.planning/research/STACK.md` — Ollama configuration, pgvector HNSW settings
- `.planning/research/PITFALLS.md` — Phase 2 pitfalls: CORS misconfiguration, Ollama unreachable from Docker, SSE parsing errors

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/config.py` — Settings singleton, all env vars already wired
- `app/db.py` — `get_pool()` asyncpg pool ready to use in repositories
- `app/models.py` — Pydantic models for `ChatRequest`, `SessionCreate`, `SessionOut`, `Mode` Literal
- `app/prompts.py` — `get_system_prompt(mode)` function returning system prompt string
- `app/routes/health.py` — Good example of asyncpg + httpx pattern for health checks

### Established Patterns
- All routes use `APIRouter` with `prefix` and `tags`
- Settings use `pydantic_settings.BaseSettings` with `.env` file
- All async DB calls use the pool pattern (`pool = await get_pool(); async with pool.acquire() as conn`)
- CORS is already configured in `main.py` with `settings.allowed_origins`

### Integration Points
- Chat route → repositories → `db.get_pool()` → Supabase Postgres
- Chat route → `app/prompts.py` → system prompt per mode
- Sessions route → repositories → DB (replace in-memory `_sessions` dict)
- Frontend (Phase 3) will consume SSE at `/api/chat` with `stream=true/false`

</code_context>

<specifics>
## Specific Ideas

- The rolling window should exclude the system prompt from the count — system prompt is prepended separately
- Token counts in usage events: Ollama `/api/chat` returns `eval_count` (completion) and `prompt_eval_count` (prompt) — use those when available
- Session mode (normal/rag/coach) determines which system prompt is used — store mode on session record
- On `stream=false`, collect full response text before returning (don't stream to a buffer)

</specifics>

<deferred>
## Deferred Ideas

### Ideas for Future Phases
- Inline citation display in chat stream (Phase 4 — RAG Foundation)
- Coach mode 2-3 lines-of-play framing (Phase 4 — RAG Foundation)
- Query embedding cache with LRU (Phase 7 — Polish)
- GPU memory monitoring endpoint (Phase 7 — Polish)

</deferred>

---

*Phase: 02-backend-core*
*Context gathered: 2026-04-22*
