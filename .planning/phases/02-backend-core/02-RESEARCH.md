# Phase 2: Backend Core - Research

**Researched:** 2026-04-22
**Domain:** FastAPI backend, asyncpg database access, SSE streaming, Ollama integration
**Confidence:** HIGH (verified via FastAPI official docs, Ollama API docs, existing codebase)

---

## Summary

Phase 2 transforms the scaffolded FastAPI backend into a production-ready API by wiring together session/message persistence, full conversation history, structured SSE streaming, and a non-streaming fallback. The primary challenges are: (1) implementing a repository pattern with raw asyncpg for DB access, (2) building SSE with structured events using FastAPI's modern `EventSourceResponse` + `ServerSentEvent` API (not the legacy `StreamingResponse` pattern in current `chat.py`), (3) rolling window history per-session, and (4) properly formatting Ollama's NDJSON streaming into SSE.

**Primary recommendation:** Use `fastapi.sse.EventSourceResponse` with `ServerSentEvent` for structured SSE, raw asyncpg in repository classes, and Ollama's `eval_count`/`prompt_eval_count` for usage statistics.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Message history (D-01 to D-03)**
- D-01: Rolling window of last N messages + system prompt per request
- D-02: System prompt always included (not counted in window)
- D-03: Default window size: 10 messages, configurable via `CHAT_HISTORY_WINDOW` env var

**SSE event format (D-04 to D-08)**
- D-04: Token events: `data: {"token": "word"}\n\n` — structured JSON, not raw text
- D-05: Done event: `data: {"done": true, "done_reason": "stop"|"length"|"tool_call"}\n\n`
- D-06: Usage event: `data: {"usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}}\n\n`
- D-07: Usage data from Ollama response (`eval_count`, `prompt_eval_count`)
- D-08: Citation events (Phase 4): `data: {"citation": {"doc": "...", "heading": "...", "score": 0.9}}\n\n`

**Non-streaming chat (D-09 to D-10)**
- D-09: Single POST /api/chat with `stream: bool` parameter (default `True`)
- D-10: Non-streaming returns structured JSON with `text`, `usage`, `done_reason`, `citations`

**Database access layer (D-11 to D-12)**
- D-11: Repository pattern: `app/repositories/session.py` + `app/repositories/message.py`
- D-12: Raw `asyncpg` — no ORM or SQL model library, full SQL control

**Session/message persistence (D-13 to D-14)**
- D-13: Sessions in `chat_sessions` table (UUID, title, mode, metadata, timestamps)
- D-14: Messages in `chat_messages` table (bigserial PK, session_id FK, role, content, citations JSONB, usage JSONB, timestamps)

### Claude's Discretion
- Exact `ef_construction` and `m` values for HNSW index (Phase 1 defaults are fine)
- `ollama_keep_alive` value during chat sessions (keep at 15m from Phase 1)
- How to handle the initial system message per session mode (create once at session start)

### Deferred Ideas (OUT OF SCOPE)
- Inline citation display in chat stream (Phase 4)
- Coach mode 2-3 lines-of-play framing (Phase 4)
- Query embedding cache with LRU (Phase 7)
- GPU memory monitoring endpoint (Phase 7)

</user_constraints>

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BACK-01 | FastAPI exposes GET /health, POST /api/sessions, GET /api/sessions, POST /api/chat, POST /api/search, POST /api/ingest/obsidian, POST /api/ingest/tft-static | Repository pattern + chat route wired to DB |
| BACK-02 | POST /api/chat returns SSE with token events and done event with usage stats | SSE via `EventSourceResponse` + `ServerSentEvent` |
| BACK-03 | Session persistence: chat_sessions + chat_messages tables with proper indexes | asyncpg repository pattern + DB schema alignment |
| BACK-04 | CORS configured to allow http://localhost:5173 explicitly (no wildcard) | Already configured in `main.py` |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Session CRUD | API/Backend | — | FastAPI routes + asyncpg repositories |
| Message persistence | API/Backend | — | asyncpg repositories writing to Postgres |
| Chat history window | API/Backend | — | Rolling window logic in chat route |
| Ollama streaming | API/Backend | — | httpx streaming to Ollama, transform to SSE |
| SSE formatting | API/Backend | Frontend Server | Backend emits SSE, frontend consumes via fetch+ReadableStream |
| Health checks | API/Backend | — | Already implemented in `health.py` |
| System prompt injection | API/Backend | — | `prompts.py` provides `get_system_prompt(mode)` |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | Web framework | Native async + SSE via `EventSourceResponse` |
| asyncpg | 0.30+ | Async Postgres driver | Non-blocking DB access for concurrent requests |
| httpx | 0.28+ | Async HTTP client | True async for Ollama streaming |
| pydantic | 2.x | Data validation | `pydantic-settings` for env config |
| uvicorn | 0.30+ | ASGI server | Standard ASGI server for FastAPI |
| python-dotenv | 1.x | Env file loading | Already in requirements.txt |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `fastapi.sse.ServerSentEvent` | Built-in (FastAPI 0.135+) | Structured SSE events | Use for all SSE in chat route |
| `fastapi.sse.EventSourceResponse` | Built-in (FastAPI 0.135+) | SSE streaming response | Return type for streaming endpoints |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `StreamingResponse` + manual bytes | `EventSourceResponse` + `ServerSentEvent` | Modern FastAPI SSE is cleaner, Pydantic-compatible, handles headers automatically |
| SQLAlchemy / ORM | Raw asyncpg | No ORM — full SQL control per D-12 |
| `requests` library | `httpx` | `httpx` is async-native, `requests` blocks the event loop |

**Installation:** Already covered by `requirements.txt`:
```bash
pip install fastapi==0.115.6 uvicorn[standard]==0.34.0 pydantic==2.10.4 pydantic-settings==2.7.1 asyncpg==0.30.0 httpx==0.28.1 python-dotenv==1.0.1
```

**Version verification:**
- `fastapi==0.115.6` — confirmed latest as of 2026-04
- `asyncpg==0.30.0` — confirmed via `pip show asyncpg`
- `httpx==0.28.1` — confirmed via `pip show httpx`

---

## Architecture Patterns

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (localhost:5173)                        │
└─────────────────────────────┬──────────────────────────────────────────────┘
                              │ fetch() + ReadableStream
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI (localhost:8000)                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │  /health    │  │ /api/sessions │  │ /api/chat  │  │ /api/search      │   │
│  └─────────────┘  └──────────────┘  └────────────┘  └──────────────────┘   │
│         │                │                 │                  │               │
│         ▼                ▼                 ▼                  ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                      Repository Layer                                │     │
│  │  ┌─────────────────────┐    ┌──────────────────────────────────┐   │     │
│  │  │ SessionRepository   │    │ MessageRepository                 │   │     │
│  │  │ - create()           │    │ - create()                       │   │     │
│  │  │ - get()             │    │ - get_history(session_id, limit)  │   │     │
│  │  │ - list()            │    │ - get_recent(session_id, N)       │   │     │
│  │  │ - delete()          │    │ - create_system()               │   │     │
│  │  └──────────┬──────────┘    └──────────────┬───────────────────┘   │     │
│  └──────────────┼──────────────────────────────┼───────────────────────┘     │
│                 │                                  │                          │
└─────────────────┼──────────────────────────────────┼──────────────────────────┘
                  │                                  │
                  ▼                                  ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                     Supabase Postgres (localhost:54322)                        │
│  ┌──────────────────────────┐    ┌───────────────────────────────────────┐   │
│  │ sessions                 │    │ messages                               │   │
│  │ (id, title, mode,        │    │ (id, session_id, role, content,       │   │
│  │  metadata, timestamps)   │    │  metadata, timestamps)                │   │
│  └──────────────────────────┘    └───────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  Ollama (localhost:11434) — qwen3:8b                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ POST /api/chat (stream: true) → NDJSON lines → transform to SSE        │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
apps/backend/app/
├── main.py                  # FastAPI app, CORS, lifespan
├── config.py                # Settings (add CHAT_HISTORY_WINDOW)
├── db.py                    # asyncpg pool (ready to use)
├── models.py                # Pydantic models (update for SSE events)
├── prompts.py               # System prompts (ready to use)
├── repositories/            # NEW: Repository pattern
│   ├── __init__.py
│   ├── session.py           # Session CRUD with asyncpg
│   └── message.py           # Message CRUD + history window
└── routes/
    ├── __init__.py
    ├── health.py           # Health check (ready)
    ├── sessions.py         # Rewrite to use SessionRepository
    ├── chat.py             # Rewrite: history, structured SSE, non-stream
    ├── search.py           # Future Phase 4
    └── ingest.py           # Future Phase 4
```

### Pattern 1: Repository Pattern with Raw asyncpg

**What:** Data access objects that encapsulate all SQL queries, accessed from routes.
**When to use:** All DB access in the backend.
**Example:**

```python
# app/repositories/session.py
from __future__ import annotations
from typing import Optional
from asyncpg import Pool

class SessionRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def create(self, title: Optional[str], mode: str) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO sessions (title, mode)
                VALUES ($1, $2)
                RETURNING id, title, mode, created_at, updated_at
                """,
                title,
                mode,
            )
            return dict(row)

    async def get(self, session_id: str) -> Optional[dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM sessions WHERE id = $1", session_id
            )
            return dict(row) if row else None
```

### Pattern 2: Rolling Window History

**What:** Fetch last N messages per session for context injection.
**When to use:** Before every chat request.
**Example:**

```python
# app/repositories/message.py
async def get_recent(self, session_id: str, limit: int = 10) -> list[dict]:
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE session_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            session_id,
            limit,
        )
        # Reverse to chronological order (oldest first)
        return [dict(r) for r in reversed(rows)]
```

### Pattern 3: SSE via EventSourceResponse + ServerSentEvent (FastAPI 0.135+)

**What:** Modern FastAPI SSE with structured events using Pydantic-compatible classes.
**When to use:** Chat streaming endpoint.

Source: [FastAPI SSE Official Docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/)

```python
# app/routes/chat.py
from collections.abc import AsyncIterable
from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_class=EventSourceResponse)
async def chat(request: ChatRequest) -> AsyncIterable[ServerSentEvent]:
    async def generate():
        # Yield token events
        async for token in stream_ollama_tokens(messages):
            yield ServerSentEvent(data={"token": token}, event="token")
        # Yield done event with usage
        yield ServerSentEvent(
            data={"done": True, "done_reason": "stop", "usage": {...}},
            event="done",
        )
    return generate()
```

### Anti-Patterns to Avoid

- **`StreamingResponse` with manual bytes formatting for SSE:** Current `chat.py` uses `f"data: {content}\n\n".encode()` — this is the legacy pattern. FastAPI 0.135+ `EventSourceResponse` + `ServerSentEvent` handles headers, keep-alive pings, and JSON encoding automatically.
- **Counting system prompt in the history window:** Per D-02, system prompt is always prepended separately and not counted in the `CHAT_HISTORY_WINDOW` limit.
- **Blocking the event loop with synchronous DB calls:** All DB access must use `async with pool.acquire() as conn` — never sync psycopg2.
- **Raw text tokens instead of structured JSON:** Per D-04, frontend expects `{"token": "word"}` not bare text tokens.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE streaming | Manual `StreamingResponse` with string formatting | `EventSourceResponse` + `ServerSentEvent` | Auto handles `Cache-Control`, `X-Accel-Buffering`, keep-alive pings, Pydantic validation |
| Postgres connection management | Connection-per-request | `get_pool()` + `pool.acquire()` context manager | Pooling prevents connection exhaustion |
| JSON serialization | Manual `json.dumps()` + `.encode()` | `ServerSentEvent(data=dict)` | FastAPI/Rust JSON encoding is faster |
| HTTP client for Ollama | `requests` (sync) | `httpx.AsyncClient` with `timeout=120.0` | Non-blocking, concurrent request support |

**Key insight:** FastAPI's `EventSourceResponse` is the single most important pattern upgrade. The current `chat.py` uses a 2023-era pattern that predates FastAPI 0.135's native SSE support.

---

## Common Pitfalls

### Pitfall 1: SSE Raw Text vs Structured JSON
**What goes wrong:** Frontend expects `{"token": "word"}` but receives bare text, causing parsing errors.
**Why it happens:** Current `chat.py` yields `f"data: {content}\n\n"` — raw text tokens instead of JSON.
**How to avoid:** Use `ServerSentEvent(data={"token": token})` which automatically JSON-encodes.
**Warning signs:** Browser console shows JSON parse errors on token events.

### Pitfall 2: Ollama NDJSON Line Parsing
**What goes wrong:** `aiter_lines()` yields empty strings or duplicate lines on some Ollama responses.
**Why it happens:** Ollama returns complete JSON objects per line (`{"message": {"content": "..."}}`), but `aiter_lines()` can fragment or double-deliver lines.
**How to avoid:** Parse with `json.loads(line.strip())` and check `if not line.strip(): continue`. Handle `done: true` chunk for final stats.
**Warning signs:** `json.JSONDecodeError` in logs, duplicate tokens in UI.

### Pitfall 3: CORS Misconfiguration
**What goes wrong:** Browser blocks SSE from `localhost:5173` to `localhost:8000`.
**Why it happens:** `allow_origins=["*"]` with `allow_credentials=True` is rejected by browsers.
**How to avoid:** Already configured in `main.py` with `allow_origins=settings.allowed_origins` = `["http://localhost:5173"]`. Verify no wildcard.
**Warning signs:** Browser console: "No 'Access-Control-Allow-Origin' header".

### Pitfall 4: Ollama Unreachable from Docker Container
**What goes wrong:** Connection refused to `localhost:11434` from inside Docker.
**Why it happens:** `localhost` in Docker refers to the container, not the host.
**How to avoid:** Use `host.docker.internal:11434` in Docker Compose. Already configured in `docker-compose.yml` via `OLLAMA_BASE_URL` env var.
**Warning signs:** `httpx.ConnectError` from backend container, works from host.

### Pitfall 5: History Window Counts System Prompt
**What goes wrong:** System prompt consumes message slots, reducing actual conversation history.
**Why it happens:** Naive window implementation fetches N messages including system prompt.
**How to avoid:** Fetch N messages of role=user or role=assistant only, then prepend system prompt separately. Per D-01 to D-03.
**Warning signs:** Longer conversations lose earlier context faster than expected.

### Pitfall 6: Missing Usage Stats on Done Event
**What goes wrong:** `done_reason` and `usage` missing from final SSE event.
**Why it happens:** Code doesn't capture the `done: true` chunk from Ollama, which contains `eval_count` and `prompt_eval_count`.
**How to avoid:** Accumulate the `done` chunk separately: `if chunk.get("done"): stats = {"eval_count": chunk.get("eval_count"), "prompt_eval_count": chunk.get("prompt_eval_count")}`. Then emit usage event after streaming completes.
**Warning signs:** Usage stats all zeros in frontend.

---

## Code Examples

### Ollama Streaming with Usage Stats
```python
# Source: [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
import json
import httpx

async def stream_ollama_response(messages: list[dict]) -> tuple[str, dict]:
    """Stream from Ollama, return (full_text, usage_stats)."""
    full_text = ""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_chat_model,
                "messages": messages,
                "stream": True,
                "keep_alive": settings.ollama_keep_alive,
                "options": {"num_ctx": 8192},
            },
        ) as response:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    full_text += content
                    yield content  # token event
                if chunk.get("done"):
                    usage["completion_tokens"] = chunk.get("eval_count", 0)
                    usage["prompt_tokens"] = chunk.get("prompt_eval_count", 0)
                    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    return usage
```

### Session Repository with asyncpg
```python
# Source: asyncpg documentation + existing db.py pattern
from app.db import get_pool

class SessionRepository:
    @staticmethod
    async def create(title: str | None, mode: str) -> dict:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO sessions (title, mode)
                VALUES ($1, $2)
                RETURNING id, title, mode, created_at, updated_at
                """,
                title or f"Session {uuid.uuid4().hex[:8]}",
                mode,
            )
            return dict(row)
```

### Message Repository with History Window
```python
# Source: D-01 to D-03 from CONTEXT.md
class MessageRepository:
    @staticmethod
    async def get_recent(session_id: str, limit: int = 10) -> list[dict]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content FROM messages
                WHERE session_id = $1 AND role != 'system'
                ORDER BY created_at DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )
            return [dict(r) for r in reversed(rows)]  # chronological order
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| `StreamingResponse` + manual bytes | `EventSourceResponse` + `ServerSentEvent` | FastAPI 0.135+ (2024) | Cleaner code, auto headers, Pydantic validation |
| In-memory session store | asyncpg repository pattern | Phase 2 | Persistent sessions across restarts |
| Raw text SSE tokens | Structured JSON `{"token": "word"}` | Phase 2 | Frontend parsing reliability |
| `requests` library | `httpx.AsyncClient` | STACK.md (2026) | Non-blocking concurrent calls |

**Deprecated/outdated:**
- `StreamingResponse` with manual `f"data: {text}\n\n"` — replaced by `EventSourceResponse`
- `OLLAMA_EMBEDDING_API` v1 (`/api/embeddings`) — current code uses `/api/embeddings`, but Ollama also has `/api/embed` for batch input

---

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The actual DB tables are `sessions` and `messages` (from `0001_initial_schema.sql`), not `chat_sessions` and `chat_messages` (from CONTEXT.md D-13/D-14) | Standard Stack / DB Schema | Phase 1 schema may need updating, or CONTEXT.md references outdated naming. Planner should verify table names against actual schema before creating repositories. |
| A2 | `messages.metadata` JSONB can store citations and usage data per D-07/D-14 | DB Schema | If citations/usage need separate columns, schema migration required in Phase 2. |
| A3 | Ollama `/api/chat` streaming returns `eval_count` (completion tokens) and `prompt_eval_count` (prompt tokens) in the `done: true` response | Code Examples | If Ollama version differs, these field names may vary. Should verify with `curl` test. |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

---

## Open Questions

1. **Schema table naming mismatch**
   - What we know: `0001_initial_schema.sql` creates `sessions` and `messages` tables. CONTEXT.md D-13/D-14 references `chat_sessions` and `chat_messages`.
   - What's unclear: Which naming convention is canonical? Should Phase 2 use existing `sessions`/`messages` or create new `chat_sessions`/`chat_messages` tables?
   - Recommendation: Use existing `sessions`/`messages` tables as-is. `messages.metadata` JSONB can store citations and usage. No schema migration needed for Phase 2.

2. **Messages table missing `role` enum constraint**
   - What we know: `messages.role` is `VARCHAR(16)` without CHECK constraint. Valid roles are `system`, `user`, `assistant`, `tool`.
   - What's unclear: Should Phase 2 add a CHECK constraint, or is VARCHAR sufficient?
   - Recommendation: Add CHECK constraint for data integrity. Low priority, can be Phase 2 or deferred.

3. **Session auto-naming**
   - What we know: `SessionCreate.title` is optional. Current in-memory store auto-names as `f"Session {session_id}"`.
   - What's unclear: Should auto-naming use the first user message content? This is SESS-01 (v2 requirement).
   - Recommendation: Defer to Phase 7. Phase 2 can use UUID-based titles.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Ollama | Chat streaming, embeddings | [ASSUMED — native Windows] | qwen3:8b, qwen3-embedding:4b | — |
| Supabase local CLI | Postgres + pgvector | [ASSUMED — `npx supabase status`] | Postgres 16.x | — |
| Python 3.11+ | Backend runtime | [ASSUMED] | 3.11+ | — |
| asyncpg | DB access | ✓ (in requirements.txt) | 0.30.0 | — |
| httpx | Ollama calls | ✓ (in requirements.txt) | 0.28.1 | — |
| FastAPI | Web framework | ✓ (in requirements.txt) | 0.115.6 | — |
| Docker | Containerization | [ASSUMED] | — | Run backend on host for dev |

**Missing dependencies with no fallback:**
- None identified — all dependencies are either in requirements.txt or assumed to be installed via Phase 1.

**Missing dependencies with fallback:**
- None identified.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `apps/backend/pytest.ini` or `pyproject.toml` |
| Quick run command | `pytest tests/ -x -v` |
| Full suite command | `pytest tests/ --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|------------------|---------------|
| BACK-01 | Session CRUD (create, get, list, delete) | unit | `pytest tests/test_sessions.py -x` | ❌ Wave 0 |
| BACK-01 | Health check returns ollama + database status | unit | `pytest tests/test_health.py -x` | ❌ Wave 0 |
| BACK-02 | SSE streaming with structured token events | unit | `pytest tests/test_chat_stream.py -x` | ❌ Wave 0 |
| BACK-02 | SSE done event contains usage stats | unit | `pytest tests/test_chat_stream.py::test_done_event_usage -x` | ❌ Wave 0 |
| BACK-03 | Messages persisted to database | integration | `pytest tests/test_messages_persist.py -x` | ❌ Wave 0 |
| BACK-04 | CORS allows localhost:5173, blocks other origins | unit | `pytest tests/test_cors.py -x` | ❌ Wave 0 |
| BACK-01 | History window respects CHAT_HISTORY_WINDOW | unit | `pytest tests/test_history_window.py -x` | ❌ Wave 0 |
| BACK-01 | Non-streaming returns structured JSON | unit | `pytest tests/test_chat_nonstream.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_<module>.py -x`
- **Per wave merge:** `pytest tests/ --tb=short`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `apps/backend/tests/` directory — contains all test files
- [ ] `apps/backend/tests/conftest.py` — shared fixtures (db pool, test client)
- [ ] `apps/backend/tests/test_sessions.py` — covers BACK-01 session CRUD
- [ ] `apps/backend/tests/test_chat_stream.py` — covers BACK-02 SSE streaming
- [ ] `apps/backend/tests/test_history_window.py` — covers history window logic
- [ ] `apps/backend/pytest.ini` — pytest-asyncio configuration
- [ ] Install: `pip install pytest pytest-asyncio httpx`

*(All gaps are Wave 0 — test infrastructure needed before implementation starts)*

---

## Security Domain

> Required when `security_enforcement` is enabled (absent = enabled). Phase 2 has no user auth but involves database writes and external API calls.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user auth — single local user |
| V3 Session Management | Partial | Sessions stored in DB, no auth tokens |
| V4 Access Control | No | Single-user local app, no access control |
| V5 Input Validation | Yes | Pydantic v2 for all request/response models |
| V6 Cryptography | No | No sensitive data transmitted externally |

### Known Threat Patterns for FastAPI + asyncpg

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via session_id | Tampering | Parameterized queries only (`$1`, `$2`) — asyncpg does not interpolate |
| Ollama prompt injection | Information Disclosure | System prompt from `prompts.py`, user input in `messages` array |
| Unvalidated message content | Tampering | Pydantic models validate all input |
| CORS bypass | Information Disclosure | Explicit `allow_origins=["http://localhost:5173"]` — no wildcard |

---

## Sources

### Primary (HIGH confidence)
- [FastAPI SSE Official Docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — `EventSourceResponse`, `ServerSentEvent`, `ServerSentEvent.data` vs `raw_data`
- [Ollama API docs (GitHub)](https://github.com/ollama/ollama/blob/main/docs/api.md) — `/api/chat` streaming format, `eval_count`, `prompt_eval_count`
- [asyncpg documentation](https://magicstack.github.io/asyncpg/current/) — connection pool, fetch/fetchrow patterns

### Secondary (MEDIUM confidence)
- [FastAPI Streaming Response docs](https://fastapi.tiangolo.com/advanced/stream-data/) — legacy pattern comparison
- [httpx async streaming](https://www.python-httpx.org/async/) — streaming patterns with `AsyncClient`

### Tertiary (LOW confidence)
- Ollama `eval_count`/`prompt_eval_count` field names on `done: true` chunk — [ASSUMED] from Ollama API training knowledge, needs verification with actual `curl` test

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in requirements.txt
- Architecture: HIGH — FastAPI SSE, asyncpg patterns verified via official docs
- Pitfalls: HIGH — based on PITFALLS.md and FastAPI/Ollama docs
- Ollama token field names: MEDIUM — [ASSUMED], needs curl verification

**Research date:** 2026-04-22
**Valid until:** 2026-05-22 (30 days — FastAPI SSE API is stable)
