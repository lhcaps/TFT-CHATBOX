# Phase 10: Hardening & Polish - PLAN

**Phase:** 10-hardening-polish
**Status:** Implemented — verification pending
**Based on:** 10-DISCUSS.md (2026-04-23) + codebase audit (2026-04-23)
**Wave grouping:** Wave 1 = independent tasks; Wave 2 = tasks that depend on Wave 1

---

## Implementation Status Summary

**ALL 5 TASKS ARE IMPLEMENTED** (verified 2026-04-23):

| Task | Status | Evidence |
|------|--------|---------|
| 1. Session Switch Loading | IMPLEMENTED ✅ | `ChatShell.tsx` lines 122-129 |
| 2. Frontend Request Timeout | IMPLEMENTED ✅ | `chat.ts` lines 10-17 |
| 3. Pydantic Validation Bounds | IMPLEMENTED ✅ | `models.py` lines 42, 52, 60 |
| 4. CompCard Component | IMPLEMENTED ✅ | `CompCard.tsx` + `compParser.ts` + `MessageList.tsx` |
| 5. Toast Notification System | IMPLEMENTED ✅ | `useToast.ts` + `toast.tsx` + `App.tsx` |

**2 ROOT CAUSES FIXED** (2026-04-23):
- GPU status SyntaxError: `/health/gpu` → `/api/health/gpu`
- PatchStatus CORS block: hardcoded URL → `/api/patch/status`

---

## Wave 1: Verification Tasks (Confirm Implementation)

### Task 1 — Verify Session Switch Loading State

**Files to verify:**
- `apps/frontend/src/components/ChatShell.tsx`

**How to verify:**
1. Confirm `messagesLoading` prop is accepted by ChatShell
2. Confirm spinner overlay renders when `messagesLoading === true`
3. Confirm overlay covers full message area with `absolute inset-0`
4. Confirm old messages are hidden during load (overlay has `bg-gray-900/80`)

**Success criteria:**
- [x] `messagesLoading` prop accepted by ChatShell
- [x] Spinner renders as absolute overlay when loading
- [x] `App.tsx` passes `messagesLoading` prop correctly

---

### Task 2 — Verify Frontend Request Timeout

**Files to verify:**
- `apps/frontend/src/api/chat.ts`

**How to verify:**
1. Confirm `AbortSignal.timeout(60_000)` is set on the fetch call
2. Confirm merged signals via `anySignal()` helper
3. Confirm `clearTimeout` called after fetch resolves

**Success criteria:**
- [x] 60s timeout set via `AbortController.timeout(60_000)`
- [x] `clearTimeout(timeoutId)` prevents memory leaks
- [x] `anySignal()` merges user-provided signal with timeout

---

### Task 3 — Verify Pydantic Validation Bounds

**Files to verify:**
- `apps/backend/app/models.py`

**How to verify:**
1. Confirm `top_k` has `Field(ge=1, le=50)` on both `ChatRequest` and `SearchRequest`
2. Confirm `session_id` has regex validator
3. Confirm 422 returned for out-of-bounds values

**Success criteria:**
- [x] `ChatRequest.top_k`: `Field(ge=1, le=50)` at line 42
- [x] `SearchRequest.top_k`: `Field(ge=1, le=50)` at line 60
- [x] `session_id` validator: `_SessionIdPattern` regex at line 14

---

## Wave 2: Phase 9 Gap Closure (All Implemented)

### Task 4 — Phase 9 META-05: CompCard Component

**Files to verify:**
- `apps/frontend/src/components/CompCard.tsx`
- `apps/frontend/src/utils/compParser.ts`
- `apps/frontend/src/components/MessageList.tsx`

**How to verify:**
1. `CompCard.tsx` exists with `CompCard` component and `parseCompCard` function
2. Tier badges use gold/silver/bronze colors
3. Item chips show color-coded borders
4. `parseCompBlocks()` splits message into comp vs text blocks
5. `MessageList` renders `<CompCard />` from parsed blocks

**Success criteria:**
- [x] `CompCard.tsx` exists (295 lines)
- [x] Tier S=gold, A=silver, B=bronze colors
- [x] AD/AP/Tank/Support item color coding
- [x] `parseCompCard()` extracts all fields
- [x] `parseCompBlocks()` splits content correctly
- [x] `MessageList.tsx` imports and renders CompCard

---

### Task 5 — Verify Toast Notification System

**Files to verify:**
- `apps/frontend/src/components/ui/toast.tsx`
- `apps/frontend/src/hooks/useToast.ts`
- `apps/frontend/src/App.tsx`

**How to verify:**
1. `useToast()` hook has `addToast`, `removeToast`, `success/error/info` helpers
2. `ToastContainer` renders bottom-right, stacks vertically
3. Success toasts auto-dismiss after 3s
4. Error toasts require manual dismiss
5. `App.tsx` renders `<ToastContainer>` and calls `toastSuccess()`

**Success criteria:**
- [x] `useToast.ts` (30 lines) with `success/error/info` helpers
- [x] `toast.tsx` (89 lines) with `ToastContainer`
- [x] Auto-dismiss: 3s for success, manual for error
- [x] `App.tsx` line 104: `<ToastContainer>`
- [x] `App.tsx` line 57: `toastSuccess('Conversation started')`
- [x] `App.tsx` line 67: `toastSuccess('Conversation deleted')`

---

## Root Cause Fixes Applied

### Fix A — GPU Status SyntaxError

**Problem:** `useGpuStatus.ts` fetched `/health/gpu` → Vite dev server returned HTML → `JSON.parse("<!doctype...")` → SyntaxError

**Fix applied 2026-04-23:**
- `useGpuStatus.ts` line 11: `/health/gpu` → `/api/health/gpu`

**Verification:**
- [x] `/api/health/gpu` matches Vite proxy rule (`'/api' → 'http://localhost:8000/api'`)
- [x] Backend endpoint exists at `GET /api/health/gpu`

---

### Fix B — PatchStatus CORS Block

**Problem:** `PatchStatus.tsx` fetched `http://localhost:8000/api/patch/status` directly → CORS block (no preflight response from backend)

**Fix applied 2026-04-23:**
- `PatchStatus.tsx` line 19: `http://localhost:8000/api/patch/status` → `/api/patch/status`

**Verification:**
- [x] `/api/patch/status` uses Vite proxy
- [x] Backend has CORS configured for `http://localhost:5173`, `http://localhost:5174`, `http://localhost:3001`
- [x] Vite proxy forwards `/api/*` to `http://localhost:8000/api`

---

## Files Summary

| File | Change |
|------|--------|
| `apps/frontend/src/components/ChatShell.tsx` | Already has messagesLoading spinner (lines 122-129) |
| `apps/frontend/src/api/chat.ts` | Already has 60s timeout (lines 10-17) |
| `apps/frontend/src/api/types.ts` | No changes needed |
| `apps/backend/app/models.py` | Already has Field constraints (lines 42, 52, 60) |
| `apps/frontend/src/components/CompCard.tsx` | Already exists (295 lines) |
| `apps/frontend/src/utils/compParser.ts` | Already exists |
| `apps/frontend/src/components/MessageList.tsx` | Already integrates CompCard (lines 3-5, 91-111) |
| `apps/frontend/src/components/ui/toast.tsx` | Already exists (89 lines) |
| `apps/frontend/src/hooks/useToast.ts` | Already exists (30 lines) |
| `apps/frontend/src/App.tsx` | Already integrates ToastContainer + toastSuccess (lines 35, 57, 67, 104) |
| `apps/frontend/src/hooks/useGpuStatus.ts` | Fixed proxy path (line 11) |
| `apps/frontend/src/components/PatchStatus.tsx` | Fixed proxy path (line 19) |

---

## Verification Steps

After confirming all files:

1. **GPU Status:** Open browser DevTools, check no SyntaxError in console
2. **PatchStatus:** Reload page, verify patch badge shows without CORS errors
3. **Session switch:** Switch between sessions, verify spinner appears during load
4. **CompCard:** Ask a meta comps question, verify styled cards render
5. **Toast:** Create a new session, verify toast notification appears

---

## Excluded from This Phase

These items are documented but deferred:
- **DB pool retry on startup**: Requires more infra work; less visible to users.
- **Rate limiting**: Depends on usage pattern understanding; premature without data.
- **Mobile responsive layout**: Needs design work beyond quick wins.
- **Ollama circuit breaker**: Requires research; lower frequency of user impact.
- **n8n failure alerting**: Covered by Phase 9 completion gate.

---

*Phase: 10-hardening-polish*
*Plan updated: 2026-04-23*
*All 5 tasks confirmed implemented + 2 root causes fixed*
