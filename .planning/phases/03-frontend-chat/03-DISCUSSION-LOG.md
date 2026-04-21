# Phase 3: Frontend Chat - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 03-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 03-frontend-chat
**Status:** Retroactively reconstructed after implementation

---

## Chat Architecture (two-hook vs one-hook)

||| Option | Description | Selected |
||--------|---------|----------|
|| Two hooks: `useSession` + `useStreamingMessages` | Session management and message streaming in separate hooks, history passed as prop | ✓ |
|| One hook: `useChat` only | Single hook owning all state | |
|| Three hooks: session/messages/chat | Maximum separation | |

**Notes:** The two-hook approach was chosen. `useSession` owns session list + current session + history loading from API. `useStreamingMessages` owns merged message state: persisted history + live SSE tokens. The history array is passed as a prop from `useSession` into `useStreamingMessages`. `App.tsx` orchestrates by passing `sessionMessages` from `useSession` into `useStreamingMessages`.

**Assumption:** Splitting concerns across two hooks is cleaner than one monolithic hook. The prop-passing pattern (`sessionMessages`) makes the data flow explicit.

**Note:** `useChat` was also created as a standalone alternative in `hooks/useChat.ts` (untracked), but the committed implementation uses `useSession` + `useStreamingMessages`.

---

## SSE Parsing (buffer accumulation)

||| Option | Description | Selected |
||--------|---------|----------|
|| Line-by-line with state machine | Parse incrementally, emit tokens as lines arrive | |
|| Buffer accumulation + split on `\n\n` | Accumulate bytes until event boundary, process complete events | ✓ |
|| Use a streaming SSE parser library | e.g. `eventsource` or custom stream parser | |

**Assumption:** The backend sends `\n\n` as the SSE event boundary (standard SSE spec). Buffer accumulation is the standard approach for SSE over `ReadableStream`.

**Assumption:** Partial events at the end of a chunk (before `\n\n`) should be preserved in a remainder and processed after the next chunk arrives or when the stream ends.

**Assumption:** Multi-line JSON within a single `data:` block should be handled by joining all `data:` lines before parsing.

---

## Abort Strategy

||| Option | Description | Selected |
||--------|---------|----------|
|| `AbortController` + `signal` passed to `fetch` | Standard Web API approach | ✓ |
|| Custom cancellation flag checked in the SSE loop | Manual polling | |
|| `reader.cancel()` directly | Low-level control, less idiomatic | |

**Assumption:** When `AbortController.abort()` is called, `fetch` will throw an `AbortError` that propagates through the reader loop. The catch block filters out `AbortError` to avoid calling `onError` for user-initiated stops.

**Assumption:** The `streamEndedRef` guard is necessary because SSE completion (`done: true`) and a reader error can both occur in quick succession. Without the guard, `onDone` and `onError` could both fire, corrupting the message state.

---

## Session State Architecture

||| Option | Description | Selected |
||--------|---------|----------|
|| Session list in `useSession` hook | Dedicated hook for session management | ✓ |
|| Session list in `App.tsx` via direct API calls | No hook, just fetch calls in handlers | |
|| localStorage persistence of sessions | Sessions survive page reload | |

**Assumption:** `useSession` should load session list on mount and allow switching, creating, and deleting sessions. Session switching should fetch both the session object and its message history.

**Assumption:** Switching sessions should clear the current message state and load the new session's history before the new session becomes active.

**Assumption:** Deleting a session while it is current should switch to the next available session or set current to null.

---

## UI Component Organization

||| Option | Description | Selected |
||--------|---------|----------|
|| Separate `Sidebar.tsx` and `EmptyState.tsx` files | Reusable components in separate files | |
|| Sidebar and EmptyState embedded in parent components | Inline in `ChatShell.tsx` and `MessageList.tsx` | ✓ |

**Assumption:** For this phase's scope, embedding Sidebar directly inside `ChatShell.tsx` (as an `<aside>` element) and EmptyState directly inside `MessageList.tsx` is simpler than creating separate files.

**Assumption:** The Stop button belongs in `ChatShell.tsx` (outside `Composer`) so it's clearly associated with the streaming state, not the input field. `Composer` focuses on composition; streaming controls belong at the chat level.

---

## UI Styling

||| Option | Description | Selected |
||--------|---------|----------|
|| CSS custom properties (Tailwind v4) | CSS variables for theme colors | ✓ |
|| Tailwind config-based theme | `tailwind.config.js` with custom colors | |
|| Dark mode by default | Dark theme, no light mode toggle | ✓ |

**Assumption:** Tailwind v4 via `@tailwindcss/vite` plugin — no `tailwind.config.js` needed. Theme colors defined as CSS custom properties in `index.css`.

**Assumption:** Enter submits, Shift+Enter inserts newline in the textarea.

**Assumption:** The textarea should auto-grow up to 120px before scrolling within itself.

---

## Backend Gap Filled During Phase 3

The frontend implementation required `GET /sessions/{id}/messages` which did not exist in the Phase 2 plan. This was identified and fixed within Phase 3 (Wave 3):

- Added `MessageRepository.get_all()` method for chronological message retrieval
- Added `GET /sessions/{id}/messages` route in `sessions.py`
- The route must be declared **before** `/{session_id}` to avoid path conflict with the route parameter

**Assumption:** Messages should be returned in chronological (ASC) order so the frontend can display them in the correct sequence.

---

## Deferred Ideas

- `useChat` standalone hook → alternative, not used in committed code
- `useSession` vs inline session management in App.tsx → settled on dedicated hook
- localStorage backup for offline resilience → Phase 7
- Token/usage display per message → Phase 7
- RAG citation cards with expandable excerpts → Phase 4 (CitationCard already exists)
- Coach mode framing with econ/tempo/cap indicators → Phase 4
- Message title auto-generation from first user message → Phase 4+
