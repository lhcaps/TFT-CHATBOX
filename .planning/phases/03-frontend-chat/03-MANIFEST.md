# Phase 3: Frontend Chat - Manifest

>**Purpose:** Records every file created or modified during phase execution, with exact change descriptions and verification signals.

**Phase:** 03-frontend-chat
**Status:** Complete
**Committed:** 2026-04-22

---

## Commits

### Commit bddb4ef — `feat(03-frontend): React chat UI with streaming, sessions, and mode tabs`

**Commits:** 1 of 2 in Phase 3

---

### Wave 1 — Types, API layer, session management

#### `apps/frontend/src/api/types.ts` (new file)

**Change:** Created shared TypeScript type definitions mirroring backend Pydantic models.

```typescript
export type Role = 'system' | 'user' | 'assistant' | 'tool';
export type Mode = 'normal' | 'rag' | 'coach';
export interface Citation { id, source, heading, text, score }
export interface Message { role, content, citations?, isStreaming? }
export interface MessageOut { role, content, citations? }
export interface Session { id, title, mode, created_at }
export interface ChatOptions { sessionId?, message, mode, stream?, signal? }
```

**Verification:**
```bash
grep -n "export type Role" apps/frontend/src/api/types.ts
grep -n "export interface Session" apps/frontend/src/api/types.ts
```

---

#### `apps/frontend/src/api/chat.ts` (modified from existing stub)

**Change:** Implemented SSE streaming client (`streamChat`) and non-streaming client (`chatNonStreaming`).

Key implementation details:
- Uses `fetch` + `ReadableStream` + `TextDecoder` (not `EventSource` — supports POST)
- Buffer accumulates bytes, split on `\n\n` for SSE event boundaries
- `parseSSEPart()` extracts `data:` lines, joins multi-line JSON, dispatches by payload shape
- `AbortController.signal` passed to `fetch`; `AbortError` caught and swallowed in catch block
- `extractEvents()` splits buffer on `\n\n`, returns `events[]` + `remainder`
- `processChunk()` flushes remainder on stream end

**Verification:**
```bash
grep -n "ReadableStream" apps/frontend/src/api/chat.ts
grep -n "extractEvents" apps/frontend/src/api/chat.ts
grep -n "AbortError" apps/frontend/src/api/chat.ts
```

---

#### `apps/frontend/src/api/sessions.ts` (new file)

**Change:** Sessions API client with full CRUD + `getSessionMessages`.

```typescript
listSessions()         // GET /api/sessions
createSession()        // POST /api/sessions
getSession(id)         // GET /api/sessions/{id}
deleteSession(id)      // DELETE /api/sessions/{id}
getSessionMessages(id) // GET /api/sessions/{id}/messages
```

All functions are async, throw on non-OK response, return typed results.

**Verification:**
```bash
grep -n "export async function" apps/frontend/src/api/sessions.ts
grep -n "getSessionMessages" apps/frontend/src/api/sessions.ts
```

---

#### `apps/frontend/src/hooks/useSession.ts` (new file)

**Change:** Created `useSession` hook — owns session list, current session, and history loading from API.

Exports: `sessions`, `currentSession`, `messages` (history), `loading`, `messagesLoading`, `error`, `loadSessions`, `switchSession`, `newSession`, `removeSession`, `setCurrentMode`.

Key behaviors:
- `switchSession(id)`: fetches fresh session data + message history, updates both `currentSession` and `messages`
- `newSession(mode)`: creates session, prepends to list, sets as current, clears messages
- `removeSession(id)`: deletes, removes from list, switches to next available or null
- `setCurrentMode(mode)`: updates mode on current session and in the sessions list
- `prevSessionIdRef` comparison detects session changes to reload history

**Verification:**
```bash
grep -n "export function useSession" apps/frontend/src/hooks/useSession.ts
grep -n "switchSession" apps/frontend/src/hooks/useSession.ts
grep -n "newSession" apps/frontend/src/hooks/useSession.ts
```

---

#### `apps/frontend/src/hooks/useStreamingMessages.ts` (new file)

**Change:** Created `useStreamingMessages` hook — owns merged message state (history + live SSE tokens).

Accepts `history: MessageOut[]` prop from `useSession`. Manages: `messages`, `isStreaming`, `error`.

Refs: `acRef` (AbortController), `tokenAccRef` (accumulated tokens), `endedRef` (double-call guard).

`toMessages()` converts API format (`MessageOut[]`) to local `Message[]` with `isStreaming: false`.

`sendMessage({ sessionId, message, mode })`:
1. Resets stream state (`endedRef`, `tokenAccRef`)
2. Appends user message + assistant placeholder (`isStreaming: true`)
3. Creates `AbortController`
4. Calls `streamChat` with callbacks

`onToken`: accumulates in `tokenAccRef`, updates last message
`onCitation`: appends citation to last message's citations array
`onDone`: guard `endedRef`, mark last message as not streaming
`onError`: guard `endedRef`, handle abort vs real error

Cleanup: `useEffect` returns `() => acRef.current?.abort()`

**Verification:**
```bash
grep -n "export function useStreamingMessages" apps/frontend/src/hooks/useStreamingMessages.ts
grep -n "endedRef" apps/frontend/src/hooks/useStreamingMessages.ts
grep -n "acRef" apps/frontend/src/hooks/useStreamingMessages.ts
```

---

### Wave 2 — App.tsx wiring

#### `apps/frontend/src/App.tsx` (modified)

**Change:** Root component rewritten to orchestrate `useSession` and `useStreamingMessages`.

```tsx
const { sessions, currentSession, messages: sessionMessages, ... } = useSession();
const { messages, isStreaming, error: chatError, sendMessage, abort, clearError } = useStreamingMessages(sessionMessages);
```

- `sessionMessages` from `useSession` passed as `history` prop to `useStreamingMessages`
- `loadSessions()` called on mount via `useEffect`
- `handleSend`: calls `sendMessage({ sessionId, message, mode: currentSession.mode })`
- `ChatShell` receives all props: messages, isStreaming, sessions, currentSession, mode handlers, abort, error
- All handlers wrapped in `useCallback`

**Verification:**
```bash
grep -n "useSession" apps/frontend/src/App.tsx
grep -n "useStreamingMessages" apps/frontend/src/App.tsx
grep -n "ChatShell" apps/frontend/src/App.tsx
```

---

#### `apps/frontend/src/components/ChatShell.tsx` (modified)

**Change:** Main layout shell with 3-column layout. Sidebar is an inline `<aside>` element (not a separate file).

Layout:
```
┌──────────────────────────────────────────────────────────┐
│ <aside w-64>              │  <header>                    │
│  [New Chat]                │  Title    [ModeTabs w-64]   │
│  [Session 1] ✓            │  ─────────────────────────── │
│  [Session 2] (hover→×)   │  <MessageList flex-1>        │
│  [Session 3]              │                              │
│                           │  ─────────────────────────── │
│                           │  <Composer>                 │
│                           │  ─────────────────────────── │
│                           │  [Stop] (when streaming)    │
└───────────────────────────┴──────────────────────────────┘
```

- Error banner: red, dismissible, shown when `error !== null`
- Stop button: positioned below Composer (`flex justify-center pb-2`), red, only when `isStreaming`
- Sidebar session items: hover-reveal mode badge + delete button via `group`/`group-hover`

**Verification:**
```bash
grep -n "aside" apps/frontend/src/components/ChatShell.tsx
grep -n "onAbort" apps/frontend/src/components/ChatShell.tsx
grep -n "isStreaming" apps/frontend/src/components/ChatShell.tsx
```

---

#### `apps/frontend/src/components/Composer.tsx` (modified)

**Change:** Auto-growing textarea, Enter-to-send, disabled during streaming.

- `useRef<HTMLTextAreaElement>` + `useEffect` on `[input]` for auto-grow
- `el.style.height = 'auto'` then `el.style.height = Math.min(el.scrollHeight, 120) + 'px'`
- `maxHeight: 120px`, `minHeight: 48px`
- `onKeyDown`: Enter submits (unless Shift held)
- `disabled` when streaming or no session
- Send button: blue, disabled when empty
- Clears input and refocuses after send
- Note: Stop button is NOT here — it lives in `ChatShell`

**Verification:**
```bash
grep -n "scrollHeight" apps/frontend/src/components/Composer.tsx
grep -n "Enter" apps/frontend/src/components/Composer.tsx
```

---

#### `apps/frontend/src/components/MessageList.tsx` (modified)

**Change:** Scrollable message list with auto-scroll, streaming indicator, empty state. EmptyState is inline (not a separate file).

- User messages: right-aligned (`justify-end`), blue background, white text
- Assistant messages: left-aligned, dark background (`bg-gray-800`)
- `useRef<HTMLDivElement>` for `bottomRef`, `useEffect` on `[messages, isStreaming]` for auto-scroll
- Streaming indicator: animated bouncing dots (`animate-bounce`, staggered delays 0/150/300ms) in assistant-style bubble
- Empty state (inline): centered chat icon SVG + helpful prompt text
- `whitespace-pre-wrap` preserves newlines
- Citations rendered via `CitationCard` components from `msg.citations`

**Verification:**
```bash
grep -n "scrollIntoView" apps/frontend/src/components/MessageList.tsx
grep -n "isStreaming" apps/frontend/src/components/MessageList.tsx
grep -n "bottomRef" apps/frontend/src/components/MessageList.tsx
```

---

#### `apps/frontend/src/components/ModeTabs.tsx` (modified)

**Change:** Three compact tab buttons in a pill-style container.

- Props: `value: Mode`, `onChange: (mode: Mode) => void`
- Inline-flex container with `bg-gray-700` background
- Active tab: `bg-blue-600 text-white`
- Inactive: `text-gray-400 hover:text-white`
- Mode labels: Normal, RAG, Coach (first letter capitalized)

**Verification:**
```bash
grep -n "export.*ModeTabs" apps/frontend/src/components/ModeTabs.tsx
grep -n "bg-blue-600" apps/frontend/src/components/ModeTabs.tsx
```

---

### Wave 3 — Tailwind v4, polish, backend fix

#### `apps/frontend/index.html` (modified)

**Change:** Updated `<title>` tag to "TFT Chatbox".

---

#### `apps/frontend/src/index.css` (modified)

**Change:** Tailwind v4 setup via `@tailwindcss/vite` plugin. Removed Tailwind directives; replaced with CSS custom properties for dark theme.

**Verification:**
```bash
grep -n "tailwindcss" apps/frontend/src/index.css
```

---

#### `apps/frontend/vite.config.ts` (modified)

**Change:** Added dev server proxy configuration.

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

**Verification:**
```bash
grep -n "proxy" apps/frontend/vite.config.ts
grep -n "localhost:8000" apps/frontend/vite.config.ts
```

---

#### `apps/backend/app/repositories/message.py` (modified)

**Change:** Added `MessageRepository.get_all()` method for chronological message retrieval.

```python
async def get_all(self, session_id: str) -> list[dict]:
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content, created_at FROM messages
            WHERE session_id = $1
            ORDER BY created_at ASC
            """,
            session_id,
        )
        return [dict(row) for row in rows]
```

Backend gap filled during Phase 3 — required by the frontend `GET /sessions/{id}/messages` endpoint.

**Verification:**
```bash
grep -n "get_all" apps/backend/app/repositories/message.py
grep -n "ORDER BY created_at ASC" apps/backend/app/repositories/message.py
```

---

#### `apps/backend/app/routes/sessions.py` (modified)

**Change:** Added `GET /sessions/{id}/messages` endpoint; refactored helper functions.

- Added `MessageOut` to imports
- Renamed `get_session_repo()` → `_session_repo()` (private)
- Added `_message_repo()` private helper
- Added `GET /sessions/{id}/messages` route (declared **before** `/{session_id}` to avoid path conflict)
- Route ordering: `GET ""`, `POST ""`, `GET /{id}/messages`, `GET /{id}`, `DELETE /{id}`

**Verification:**
```bash
grep -n "get_session_messages" apps/backend/app/routes/sessions.py
grep -n "messages" apps/backend/app/routes/sessions.py
```

---

### Commit 1154692 — `docs(phase-3): mark Frontend Chat complete in roadmap and add phase context`

**Commits:** 2 of 2 in Phase 3

#### `.planning/ROADMAP.md` (modified)

**Change:** Marked Phase 3 complete in the progress table.

---

#### `.planning/phases/03-frontend-chat/03-CONTEXT.md` (new file)

**Change:** Created phase context with decisions (D-01 to D-17), architecture, canonical references, and deferred ideas.

---

## File Inventory (Phase 3)

| File | Type | Commit | Status |
|------|------|--------|--------|
| `apps/frontend/src/api/types.ts` | new | bddb4ef | ✅ |
| `apps/frontend/src/api/chat.ts` | modified | bddb4ef | ✅ |
| `apps/frontend/src/api/sessions.ts` | new | bddb4ef | ✅ |
| `apps/frontend/src/hooks/useSession.ts` | new | bddb4ef | ✅ |
| `apps/frontend/src/hooks/useStreamingMessages.ts` | new | bddb4ef | ✅ |
| `apps/frontend/src/App.tsx` | modified | bddb4ef | ✅ |
| `apps/frontend/src/components/ChatShell.tsx` | modified | bddb4ef | ✅ |
| `apps/frontend/src/components/Composer.tsx` | modified | bddb4ef | ✅ |
| `apps/frontend/src/components/MessageList.tsx` | modified | bddb4ef | ✅ |
| `apps/frontend/src/components/ModeTabs.tsx` | modified | bddb4ef | ✅ |
| `apps/frontend/src/components/CitationCard.tsx` | modified | bddb4ef | ✅ |
| `apps/frontend/index.html` | modified | bddb4ef | ✅ |
| `apps/frontend/src/index.css` | modified | bddb4ef | ✅ |
| `apps/frontend/vite.config.ts` | modified | bddb4ef | ✅ |
| `apps/frontend/package-lock.json` | modified | bddb4ef | ✅ |
| `apps/backend/app/repositories/message.py` | modified | bddb4ef | ✅ |
| `apps/backend/app/routes/sessions.py` | modified | bddb4ef | ✅ |
| `.planning/ROADMAP.md` | modified | 1154692 | ✅ |
| `.planning/phases/03-frontend-chat/03-CONTEXT.md` | new | 1154692 | ✅ |

> **Note:** `Sidebar.tsx` and `EmptyState.tsx` are **not** separate files. The sidebar markup is inline within `ChatShell.tsx` (as an `<aside>` element), and the empty state is inline within `MessageList.tsx`.

---

## Verification Checklist

### TypeScript
```bash
cd apps/frontend && npx tsc --noEmit
```
Expected: 0 errors

### Vite Build
```bash
cd apps/frontend && npm run build
```
Expected: Clean production build (35 modules, ~158 KB JS gzipped ~50 KB per commit notes)

### Backend (sessions/messages endpoint)
```bash
cd apps/backend && python -c "from app.routes.sessions import router; print('OK')"
```
Expected: `OK`

### Functional checks
- [ ] App loads at `http://localhost:5173`
- [ ] Session list loads in sidebar on mount
- [ ] New Chat creates a session and switches to it
- [ ] Mode tabs switch between Normal/RAG/Coach
- [ ] Typing a message and pressing Enter (not Shift) sends it
- [ ] Assistant response streams in real-time with animated dots
- [ ] Stop button (shown during streaming) aborts the stream
- [ ] Switching sessions loads that session's message history
- [ ] Deleting a session removes it from the list
- [ ] TypeScript compiles with 0 errors
- [ ] Vite production build succeeds

---

*Phase: 03-frontend-chat*
*Status: Complete*
*Commits: bddb4ef, 1154692*
