# Phase 3: Frontend Chat - Context

**Gathered:** 2026-04-22
**Status:** Complete

<domain>
## Phase Boundary

Build the React frontend scaffold into a fully functional chat UI: SSE streaming with real-time token display, session management (create/switch/delete), three-mode toggle (Normal/RAG/Coach), message history persistence, and a dark-mode dark theme.

**Scope:** `apps/frontend/` React app with Vite, Tailwind v4, SSE streaming, session sidebar, mode tabs, message history, streaming tokens, Stop/abort button.
**Out of scope:** RAG retrieval UI, Coach prompting (Phase 4), n8n automation (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Frontend architecture (D-01 to D-03)
- **D-01:** React 18 + Vite 6 + Tailwind v4 (via `@tailwindcss/vite` plugin)
- **D-02:** No routing library — single-page app, session switching handled in-memory via hooks
- **D-03:** No external state management — React hooks (`useState`, `useRef`, `useCallback`, `useEffect`) as state container

### API integration (D-04 to D-06)
- **D-04:** Vite dev server proxy: `/api/*` → `http://localhost:8000` (avoids CORS in dev)
- **D-05:** SSE streaming via `fetch` + `ReadableStream` + `TextDecoder` — no EventSource (EventSource can't send POST)
- **D-06:** SSE event types: `token` (streaming word), `done` (completion), `citation` (Phase 4), `error` (error) — all parsed from `data: {json}\n\n` blocks

### Session state management (D-07 to D-09)
- **D-07:** `useSession` hook owns session list + current session + session history from API
- **D-08:** `useStreamingMessages` hook owns merged message state: persisted history + live SSE tokens. Accepts history as a prop; emits streaming tokens in real-time.
- **D-09:** `App.tsx` orchestrates: passes `sessionMessages` from `useSession` into `useStreamingMessages`, renders `ChatShell`

### Message state (D-10 to D-12)
- **D-10:** Messages stored as `Message[]` in `useStreamingMessages` — single source of truth
- **D-11:** Token accumulation: `streamingTokenRef` accumulates SSE tokens, flushed into `messages` state on each token event (avoids React re-render on every character)
- **D-12:** `streamEndedRef` guard prevents double-calling `onDone`/`onError` callbacks when SSE completes and stream also errors

### UI layout (D-13 to D-14)
- **D-13:** Sidebar (256px) + main chat area. Sidebar: session list with New Chat button, mode badge, delete button (hover-revealed)
- **D-14:** Main area: header with session title + mode tabs, error banner, scrollable message list, auto-growing composer, Stop button (shown during streaming)

### SSE parsing (D-15 to D-17)
- **D-15:** Buffer accumulates bytes until `\n\n` (SSE event boundary). Partial events preserved in remainder.
- **D-16:** `extractEvents()` splits on `\n\n`, calls `parseSSEPart()` per block
- **D-17:** `parseSSEPart()` extracts all `data: ` lines, joins JSON, dispatches by payload shape (`token`/`citation`/`done`/`error`)

</decisions>

<canonical_refs>
## Canonical References

### Project context
- `.planning/PROJECT.md` — Vision, stack, constraints, TFT policy compliance
- `.planning/REQUIREMENTS.md` — FRONT-01 to FRONT-05
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria, dependencies
- `.planning/phases/02-backend-core/02-CONTEXT.md` — Backend decisions (SSE format, mode system, session persistence)

### Existing code (read before implementing)
- `apps/backend/app/routes/chat.py` — SSE endpoint with token/done/usage events
- `apps/backend/app/routes/sessions.py` — Sessions CRUD + `GET /sessions/{id}/messages`
- `apps/backend/app/repositories/message.py` — `MessageRepository.get_all()` for chronological retrieval
- `apps/frontend/vite.config.ts` — Vite config with proxy to backend
- `apps/frontend/package.json` — React 18, Vite 6, Tailwind v4

### Key files created
- `apps/frontend/src/api/types.ts` — Shared TypeScript types
- `apps/frontend/src/api/chat.ts` — SSE streaming client
- `apps/frontend/src/api/sessions.ts` — Sessions API client
- `apps/frontend/src/hooks/useSession.ts` — Session management hook
- `apps/frontend/src/hooks/useStreamingMessages.ts` — Message + streaming hook
- `apps/frontend/src/components/ChatShell.tsx` — Main layout component
- `apps/frontend/src/components/MessageList.tsx` — Scrollable message list
- `apps/frontend/src/components/Composer.tsx` — Auto-growing input
- `apps/frontend/src/components/ModeTabs.tsx` — Normal/RAG/Coach tabs

</canonical_refs>

<code_context>
## Code Architecture

### Hook dependency graph
```
App.tsx
  └── useSession() → api/sessions.ts → GET /sessions, POST /sessions, DELETE /sessions, GET /sessions/{id}/messages
        └── sessionMessages[] (history from API)
              └── useStreamingMessages(sessionMessages)
                    ├── api/chat.ts → POST /api/chat (SSE)
                    │     └── streamChat() → SSE → onToken/onCitation/onDone/onError
                    └── messages[] (history + live tokens)
                          └── ChatShell → MessageList + Composer + ModeTabs
```

### API endpoints consumed
- `GET /api/sessions` — list all sessions
- `POST /api/sessions` — create session
- `GET /api/sessions/{id}` — get session
- `GET /api/sessions/{id}/messages` — get session messages
- `DELETE /api/sessions/{id}` — delete session
- `POST /api/chat` — SSE chat (streaming=true)

### Established patterns
- All React components use TypeScript with strict types
- Hooks use `useCallback` for event handlers passed as props
- SSE uses `ReadableStream` + `TextDecoder` (not EventSource for POST requests)
- Tailwind v4 via `@tailwindcss/vite` — no tailwind.config.js needed

</code_context>

<specifics>
## Specific Ideas

- Auto-scroll: `useEffect` watching `messages` + `isStreaming` → `bottomRef.current?.scrollIntoView({ behavior: 'smooth' })`
- Auto-grow textarea: set `style.height = 'auto'` then `style.height = el.scrollHeight` on each `onChange`
- Enter to send, Shift+Enter for newline: check `e.key === 'Enter' && !e.shiftKey`
- Stop button: `AbortController.abort()` sent via `signal` to `fetch`, SSE loop exits with `AbortError`
- Session switch detection: `prevSessionIdRef` ref compares current vs previous `currentSession.id`
- Mode tabs: `currentMode` prop drives active tab styling, mode stored on session object

</specifics>

<deferred>
## Deferred Ideas

### Ideas for Future Phases
- Message title auto-generation from first user message (Phase 4+)
- localStorage backup of sessions for offline resilience (Phase 7)
- Token/usage display per message (Phase 7)
- RAG citation cards with expandable excerpts (Phase 4)
- Coach mode framing with econ/tempo/cap indicators (Phase 4)

</deferred>

---

*Phase: 03-frontend-chat*
*Context gathered: 2026-04-22*
*Status: Complete*
