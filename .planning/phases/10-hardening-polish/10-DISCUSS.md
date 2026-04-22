# Phase 10: Hardening & Polish - DISCUSS

**Phase:** 10-hardening-polish
**Status:** Discuss — gathering context before planning
**Gathered:** 2026-04-23
**Source:** Codebase audit + prior phase artifacts

---

## A) Current System Health

### Error Handling

| Location | What exists | Gap |
|----------|-------------|-----|
| `apps/frontend/src/hooks/useStreamingMessages.ts` | `AbortError` detection, error state with `setError`, graceful fallback message rendered in chat UI | No retry/auto-retry on transient errors; no toast for non-stream errors |
| `apps/frontend/src/hooks/useSession.ts` | Try/catch on all API calls, `sessionsError` + `sessionsError` surfaced to `App.tsx` | Error messages are raw `Error.message` — no user-friendly formatting |
| `apps/frontend/src/api/chat.ts` | `fetch` with `!res.ok` throw, SSE parse errors silently skipped | No request timeout on the fetch level; network errors not handled distinctly from API errors |
| `apps/backend/app/routes/chat.py` | `try/except` around `build_messages` and `chat_non_streaming`, DB write failure is silently swallowed (`pass`) | Ollama connection errors only yield SSE `error` event mid-stream — no proactive health pre-check; no request timeout on the httpx client beyond the hard 120s default |
| `apps/backend/app/routes/health.py` | Checks both Ollama (`/api/tags`) and database (`SELECT 1`) with 5s timeouts | No structured health aggregation (e.g., readygrip check); health endpoint not consumed by frontend |
| `apps/backend/app/routes/ingest.py` | Try/catch with `logger.exception` on all ingest endpoints, `patch_info` status tracking | No retry logic for transient failures; ingest errors bubble as 500 with raw exception string |

### Retry Logic

**None exists at any layer.** If Ollama is temporarily unavailable, the chat stream returns an error event and the user must manually retry. No exponential backoff, no circuit breaker.

### Timeouts

| Layer | Value | Issue |
|-------|-------|-------|
| `httpx.AsyncClient` in `chat.py` | 120s hard-coded | No per-phase timeout (connect vs read vs write); 120s may not be enough for slow embedding lookups |
| `httpx.AsyncClient` in `health.py` | 5s | OK |
| Frontend `fetch` | Browser default (no `AbortSignal` timeout set) | No client-side timeout — a stalled request holds the UI indefinitely |
| DB pool (`db.py`) | asyncpg default | No `command_timeout`, `query_timeout` configured |

### Validation

| Location | What's validated | What's missing |
|----------|-----------------|----------------|
| `ChatRequest` (`models.py`) | `session_id`, `message`, `mode`, `stream` | No `message` length limit; no sanitization of special characters |
| `SearchRequest` (`models.py`) | `query`, `top_k`, `patch` | `top_k` has no upper bound (could pass `top_k=99999`) |
| Session IDs | Passed through to DB | No UUID format validation on `session_id` before DB query |
| `mode` | Literal enum (`normal`, `rag`, `coach`) | Covered by Pydantic |

---

## B) Frontend Polish

### Loading States

| Component | Current state | Gap |
|-----------|--------------|-----|
| `ChatShell` sidebar | `loading && sessions.length === 0` → "Loading..." | No skeleton loader; spinner not shown; blank screen between mount and first API response |
| Session switch | `messagesLoading` state tracked but **not rendered** anywhere | User has no feedback when switching sessions; old messages stay visible during load |
| Send button / Composer | `disabled` prop while `isStreaming` or no `currentSession` | No loading indicator on the send action itself |

### Empty States

| Place | Current | Gap |
|-------|---------|-----|
| Sidebar with no sessions | "No sessions yet" text | Static text only — no illustration, no CTA prompt |
| Message list empty | Composer always visible | No "Start a conversation" prompt when no messages exist |
| Search results empty | N/A (no dedicated search UI) | N/A |

### Error UX

| Place | Current | Gap |
|-------|---------|-----|
| Chat error | Red banner in `ChatShell`, dismiss button | Banner only — no toast, no retry button, no distinction between "network error" vs "Ollama down" |
| Session load error | Silently swallows error, clears messages | No error shown to user for failed session loads |

### Toast Notifications

**None exist.** All feedback is either inline (error banner) or absent.

### Mobile / Responsive

- `ChatShell` uses fixed `w-64` sidebar + full-width main — works on tablet, likely broken on phone
- `Composer` has no mobile adaptations
- No `viewport` meta tag check confirmed; `h-screen` + `overflow-hidden` could cause issues on iOS Safari

---

## C) Backend Hardening

### DB Connection Resilience

| Issue | Current state | Gap |
|-------|--------------|-----|
| Pool init | `asyncpg.create_pool` in `get_pool()`, lazy singleton | No retry on initial pool creation failure; if DB is down at startup, every request fails |
| Connection reuse | Pool with `min_size=2, max_size=10` | No health check / reconnect on stale connections |
| Pool shutdown | `close_pool()` called on `lifespan` shutdown only | If DB connection drops mid-life, pool is not rebuilt |
| Query timeouts | No `command_timeout` set on pool | Long queries can block the pool indefinitely |

### Health Checks

| Check | Current | Gap |
|-------|---------|-----|
| Backend self-check | `GET /api/health` returns `ollama` + `database` status | Not called by frontend; no readygrip for Docker/liveness probes |
| Ollama availability | Checked before each chat request only as a fallback | No proactive pre-flight check |
| Frontend health | None | App has no "system OK" indicator; GPU badge only shows Ollama GPU status |

### Input Validation

See Section A — Pydantic models are basic with missing bounds.

### Rate Limiting

**None.** The chat endpoint is open. A runaway client (or a bug loop) can flood Ollama with unbounded concurrent requests.

---

## D) Phase 9 MetaTFT Gaps

From `09-SPEC.md` and `09-CONTEXT.md`, the following items are specified but not yet evaluated for completeness:

| ID | Spec item | Status | Gap |
|----|-----------|--------|-----|
| META-01 | `POST /api/ingest/metatft` endpoint | **Implemented** (`ingest.py` L168) | No error retry; no dedup verification; `source='metatft'` tag needs verification in DB |
| META-02 | MetaTFT → Markdown transformer | **Implemented** (`scrape_metatft.py`) | No validation that output format matches LLM prompt expectations |
| META-03 | Space Gods set data ingest (patch 17.1 + set overview) | **Implemented** (`scrape_set_overview.py`, `scrape_metatft.py`) | No verification that ingested chunks are retrievable |
| META-04 | n8n daily MetaTFT trigger (12:00 noon) | **Partially done** (workflow exists, trigger TBD) | Discord notifications on failure not verified; no alert if ingest returns 0 chunks |
| META-05 | Frontend `CompCard` component | **Not implemented** | The LLM is supposed to output markdown comp card syntax, but no frontend component renders it specially — it falls through to plain `MessageList` rendering |

**Critical gap:** The Phase 9 spec promises `CompCard` rendering (`D-08`), but the frontend has no component to parse and display structured comp data. This is the single largest Phase 9 gap.

---

## E) Top 5 Prioritized Items

Ranked by: **impact × likelihood of user hitting it × effort to fix**.

| # | Item | Rationale | Effort |
|---|------|-----------|--------|
| **1** | **Phase 9 CompCard component** | Phase 9 is incomplete without this. MetaTFT data gets ingested but never rendered as a card — user gets raw markdown. High visibility gap. | Medium |
| **2** | **Frontend toast notification system** | Errors are invisible on mobile and easy to miss on desktop. A toast library (e.g., `react-hot-toast`) with a shared `useToast` hook would dramatically improve UX for all error/success states. | Low |
| **3** | **Session switch loading state** | `messagesLoading` is tracked but never rendered. Users see stale messages during a session switch, which looks broken. A 5-line spinner fix resolves this. | Low |
| **4** | **Chat request timeout + retry hint** | Frontend `fetch` has no timeout. A stalled Ollama request hangs the UI indefinitely. Adding a 60s `AbortSignal` timeout + showing a "Ollama is slow, try again" message is a 10-line fix with high value. | Low |
| **5** | **Input validation bounds** | `top_k` has no upper bound; `session_id` is unsanitized. These are correctness/security gaps that could cause DB issues or unexpected behavior. A Pydantic `Field` constraint + session ID regex is ~5 lines. | Low |

**Items deprioritized for this phase** (good to do later, lower urgency):
- DB pool retry on initial failure (requires more infra work)
- Rate limiting (depends on understanding usage patterns first)
- Mobile responsive layout (requires design work)
- Ollama circuit breaker (requires research into best pattern)
- n8n failure alerting (low user impact, covered by Phase 9)

---

## Open Questions for Discuss

1. **CompCard scope**: Should `CompCard` handle only MetaTFT comps, or be a general-purpose "structured data card" for any structured LLM output (items, champions, etc.)?
2. **Toast library**: `react-hot-toast` vs custom? Any existing preferences in the project?
3. **Phase 9 verification**: Should Phase 10 include a verification task that confirms META-01 through META-04 actually work end-to-end before adding CompCard?
4. **Phase 9 completion gate**: Should CompCard (META-05) be part of Phase 10 since Phase 9 is incomplete, or should it be a separate follow-up?

---

*Phase: 10-hardening-polish*
*Context gathered: 2026-04-23 via codebase audit*
