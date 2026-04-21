# Plan 02-03 Summary: Chat Endpoint

**Phase:** 02-backend-core
**Plan:** 03
**Status:** Completed
**Executed:** 2026-04-22

## Tasks Completed

### Task 1: Rewrite chat.py with structured SSE, history windowing, and non-streaming support

**File modified:** `apps/backend/app/routes/chat.py`

**Implementation:**

1. **Imports:** Added structured SSE imports (`EventSourceResponse`, `ServerSentEvent`), `JSONResponse`, `MessageRepository`, `get_system_prompt`, and `get_pool`.

2. **`build_messages()` helper:** Builds the messages array for Ollama with:
   - System prompt (prepended, not counted in window)
   - Recent conversation history (last N messages from DB)
   - Current user message

3. **`stream_ollama_tokens()` helper:** Streams tokens from Ollama as structured SSE events:
   - Yields `ServerSentEvent(data={"token": content})` for each token (per D-04)
   - Yields `ServerSentEvent(data={"done": true, "done_reason": ..., "usage": ...})` on completion (per D-05, D-06)
   - Extracts usage stats from Ollama's `eval_count` and `prompt_eval_count` (per D-07)
   - Persists assistant message to DB after stream completes

4. **`chat_non_streaming()` helper:** Non-streaming mode:
   - Makes a single non-streaming request to Ollama
   - Returns structured JSON with `text`, `usage`, `done_reason`, `citations` (per D-10)
   - Persists assistant message to DB

5. **`POST /chat` endpoint:** Main chat endpoint with:
   - `stream=true` (default): Returns SSE with `EventSourceResponse` + structured token/done/usage events
   - `stream=false`: Returns `JSONResponse` with complete response
   - Persists user message BEFORE streaming starts
   - Persists assistant message AFTER streaming completes

## Verification Results

| Check | Status |
|-------|--------|
| `EventSourceResponse` imported and used | PASS |
| `ServerSentEvent` imported and used | PASS |
| `build_messages()` implemented | PASS |
| `stream_ollama_tokens()` implemented | PASS |
| `chat_non_streaming()` implemented | PASS |
| `MessageRepository` used | PASS |
| `get_system_prompt()` called | PASS |
| `settings.chat_history_window` used | PASS |
| `eval_count` extracted | PASS |
| `prompt_eval_count` extracted | PASS |
| `get_recent()` called | PASS |
| User message persisted before streaming | PASS |
| Assistant message persisted after streaming | PASS |
| `JSONResponse` used for non-streaming | PASS |
| No raw `f"data: {content}\n\n"` strings | PASS |

## Acceptance Criteria

- [x] `EventSourceResponse` and `ServerSentEvent` imported and used for streaming
- [x] `build_messages()` prepends system prompt, then adds recent history, then user message
- [x] `build_messages()` calls `MessageRepository.get_recent()` with `settings.chat_history_window`
- [x] `stream_ollama_tokens()` yields `ServerSentEvent(data={"token": ...})` for each token (per D-04)
- [x] `stream_ollama_tokens()` yields done event with `done`, `done_reason`, `usage` (per D-05, D-06)
- [x] Usage stats extracted from Ollama's `eval_count` and `prompt_eval_count` (per D-07)
- [x] `chat_non_streaming()` returns dict with `text`, `usage`, `done_reason`, `citations` (per D-10)
- [x] User message persisted via `MessageRepository.create(role="user")` BEFORE streaming starts
- [x] Assistant message persisted via `MessageRepository.create(role="assistant")` AFTER streaming completes
- [x] Non-streaming returns `JSONResponse` (not EventSourceResponse)
- [x] No raw `f"data: {content}\n\n"` strings anywhere in the file

## API Behavior

### Streaming Mode (stream=true)

```
POST /chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "What comps are good?",
  "mode": "rag",
  "stream": true
}
```

**Response:** SSE stream with events:
- `event: token` → `data: {"token": "..."}`
- `event: done` → `data: {"done": true, "done_reason": "stop", "usage": {...}}`

### Non-Streaming Mode (stream=false)

```
POST /chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "What comps are good?",
  "mode": "rag",
  "stream": false
}
```

**Response:** JSON
```json
{
  "text": "response text",
  "usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N},
  "done_reason": "stop",
  "citations": []
}
```

## Files Modified

- `apps/backend/app/routes/chat.py` — Complete rewrite with structured SSE, history windowing, non-streaming support

## Dependencies

- Requires: Phase 01 (repositories, config, prompts, models)
- Provides: Core chat functionality for Phase 03 (Frontend Chat)

## Commit

```
feat(02-03): implement structured SSE chat endpoint with history windowing
```

---

*Plan 02-03 executed: 2026-04-22*
