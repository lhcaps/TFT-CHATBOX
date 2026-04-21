# Phase 2: Backend Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 2-backend-core
**Areas discussed:** Message history, SSE format, Non-streaming chat, Database access layer

---

## Message History

|| Option | Description | Selected |
|--------|---------|----------|
| Last N messages (rolling window) | Efficient, prevents context overflow, configurable size | |
| Full conversation history | Preserves all context, but risks hitting token limits | |
| Last N + system prompt only | Cleanest separation, no confusion | ✓ |
| AI decides | Pick whatever works best for the Ollama model | |

**User's choice:** Last N + system prompt only
**Notes:** Clean separation between conversation context and system framing. System prompt always prepended separately.

|| Option | Description | Selected |
|--------|---------|----------|
| 10 messages | Good balance for TFT follow-ups (default) | ✓ |
| 20 messages | More context for longer strategy discussions | |
| 5 messages | Minimal, keeps responses focused and fast | |
| AI decides | Pick what works best for qwen3:8b | |

**User's choice:** 10 messages
**Notes:** Configurable via CHAT_HISTORY_WINDOW env var.

---

## SSE Event Format

|| Option | Description | Selected |
|--------|---------|----------|
| Simple: raw token text | Frontend reconstructs the message | |
| Structured: token + done + usage events | Clean, explicit event types | ✓ |
| Hybrid: plain text tokens + JSON done/usage | Mix of approaches | |

**User's choice:** Structured events
**Notes:** Each event is JSON: `{"token": "..."}`, `{"done": true, "done_reason": "..."}`, `{"usage": {...}}`

|| Option | Description | Selected |
|--------|---------|----------|
| Minimal: just {"done": true} | Frontend manages all state | |
| With usage: done + token counts | Prompt/completion/total tokens | |
| With usage + done_reason: stop/length/tool_call | Most complete | ✓ |

**User's choice:** Usage + done_reason
**Notes:** Ollama's eval_count and prompt_eval_count used for token counts.

---

## Non-Streaming Chat

|| Option | Description | Selected |
|--------|---------|----------|
| stream=false parameter | Same endpoint, cleaner API surface | ✓ |
| Separate /api/chat/sync endpoint | Clearer intent, easier to reason about | |
| AI decides | | |

**User's choice:** stream=false parameter
**Notes:** Single consistent endpoint with optional streaming.

|| Option | Description | Selected |
|--------|---------|----------|
| Plain text string | Simplest, works for basic clients | |
| Structured JSON: text/usage/citations | More useful for debugging | ✓ |

**User's choice:** Structured JSON
**Notes:** Response shape: `{text, usage, done_reason, citations: []}`

---

## Database Access Layer

|| Option | Description | Selected |
|--------|---------|----------|
| Repository pattern: app/repositories/ | Clean separation, testable | ✓ |
| Service layer: app/services/ | Consistent with existing services/ | |
| Inline in routes | Keep it simple for MVP | |

**User's choice:** Repository pattern
**Notes:** `app/repositories/session.py` + `app/repositories/message.py`

|| Option | Description | Selected |
|--------|---------|----------|
| Raw asyncpg | Minimal abstraction, full SQL control, no magic | ✓ |
| Pydantic/TypeORM-style models | Cleaner but adds a dependency | |
| AI decides | | |

**User's choice:** Raw asyncpg
**Notes:** No ORM, no SQL model library — full control over SQL.

---

## Claude's Discretion

The following were left to Claude's judgment:
- Exact HNSW ef_construction and m values (Phase 1 defaults are fine)
- ollama_keep_alive value during chat sessions (keep at 15m from Phase 1)
- How to handle the initial system message per session mode (create once at session start)

---

## Deferred Ideas

- Inline citation display in chat stream → Phase 4 (RAG Foundation)
- Coach mode 2-3 lines-of-play framing → Phase 4 (RAG Foundation)
- Query embedding cache with LRU → Phase 7 (Polish)
- GPU memory monitoring endpoint → Phase 7 (Polish)
