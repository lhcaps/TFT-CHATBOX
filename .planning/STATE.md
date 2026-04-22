# STATE: TFT Local Copilot

**Project:** TFT Local Copilot
**Last updated:** 2026-04-23

---

## Project Reference

**Core Value:** A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem.

**Current Milestone:** v1.3 Hardening & Polish — shipped

---

## Current Position

**Active Phase:** Phase 10 complete — all milestones shipped

**Milestone Progress:**
```
✅ v1.0 MVP — Phases 1-7 (shipped 2026-04-22)
✅ v1.1 TFT Meta Mastery — Phase 8 (shipped 2026-04-22)
✅ v1.2 MetaTFT Real-time Intelligence — Phase 9 (shipped 2026-04-23)
✅ v1.3 Hardening & Polish — Phase 10 (shipped 2026-04-23)
```

**Root Cause Fixes Applied (2026-04-23):**
- Fix A: GPU status SyntaxError — `/health/gpu` → `/api/health/gpu` in `useGpuStatus.ts`
- Fix B: PatchStatus CORS block — hardcoded URL → `/api/patch/status` via Vite proxy

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| v1.0 Requirements mapped | 35/35 | 100% coverage |
| v1.0 Phases defined | 7 | All complete |
| v1.0 Smoke test | 60/60 PASS | 20 questions × 3 modes |
| v1.1 Requirements | 5/5 | PATCH-01..05 complete |
| v1.2 Requirements (META) | 5/5 | META-01..05 complete |
| v1.3 Requirements (HARD) | 5/5 | HARD-01..05 complete |
| Total Phases shipped | 10 | Phases 1-10 all shipped |

---

## Hardware Context

| Resource | Capacity | Usage |
|----------|---------|-------|
| RAM | 64GB | Full system |
| VRAM | 12GB (RTX 4070 Ti SUPER) | Chat + Embedding models |
| Chat model | qwen3:1.7b | ~1.4GB VRAM |
| Embedding model | qwen3-embedding:4b | ~2.5GB VRAM (2560 dims → 1024 truncated) |

---

## Stack Summary

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 19 + Vite 6 + Tailwind 4 | Chat UI |
| Backend | FastAPI + Uvicorn | API orchestration |
| LLM | Ollama native (Windows) | qwen3:1.7b + qwen3-embedding:4b |
| Database | Supabase local CLI (pgvector/HNSW) | 1024-dim embeddings |
| Automation | n8n (Docker) | Scheduled workflows |
| Knowledge | Obsidian vault | Markdown notes |
| TFT Data | Riot CDN + CommunityDragon + Patch page scrape | Set 17 Space Gods, Patch 17.1 |

---

## Key Decisions (Locked)

| Decision | Rationale | Status |
|----------|-----------|--------|
| Ollama native (not containerized) | GPU passthrough on Windows | ✅ Locked |
| 1024-dim embeddings | HNSW index limit 2000 dims, qwen3-embedding:4b truncates to 1024 | ✅ Locked |
| Supabase local CLI | Postgres + pgvector without Docker complexity | ✅ Locked |
| 3-mode chat (Normal/RAG/Coach) | TFT policy compliance | ✅ Locked |
| SSE for streaming | Sufficient for one-way streaming | ✅ Locked |
| In-memory LRU cache | MVP scale doesn't need Redis | ✅ Locked |
| Bearer token auth | Defense in depth | ✅ Locked |
| ngrok dropped | 100% local, no remote access needed | ✅ Locked |
| RLS disabled | Local-only, risk accepted | ✅ Locked |

---

## Accumulated Context

### v1.1 TFT Meta Mastery — SHIPPED ✅

**All features delivered:**
- `patch_info` table: current_patch, latest_available, last_checked, last_ingested, ingest_status, patch_notes_url, updated_at
- `GET /api/patch/status` → full DB state with is_stale
- `POST /api/patch/status/refresh` → update latest_available from Riot CDN
- `POST /api/ingest/patch-notes` → scrape + ingest patch notes chunks
- `scrape_patch_url()` → listing page discovery, URL pattern fallback
- n8n `patch_monitor.json` → `active: true`, calls both ingest endpoints, Discord start/success/fail
- `PatchStatus` component → version badge, stale indicator, check button in header

**Outstanding:**
- n8n workflow needs user to open http://localhost:5678 and configure API key + Discord webhook credentials
- `scrape_patch17.py` hardcodes Set 17 URL template — needs update for future sets

**Goal:** Automated TFT meta intelligence — backend tracks patch state in DB, n8n monitors Riot for new patches, auto-ingests patch notes + static data when available.

**Gap Analysis (from codebase audit):**
1. `patch_monitor.json` exists but `"active": false` — not running
2. `patch_state.py` reads from file `latest_version.txt`, not DB
3. No `patch_info` table in DB — no structured patch metadata storage
4. `scrape_patch17.py` is one-off script, not API-triggered
5. n8n `patch_monitor` only triggers `/ingest/tft-static`, NOT patch notes scraping
6. Frontend has no patch version display or staleness indicator

**What was built:**
1. DB `patch_info` table: stores current_patch, latest_available, last_checked, last_ingested
2. Backend API: `GET /api/patch/status` (returns current + latest + staleness)
3. Backend API: `POST /api/ingest/patch-notes` — scrapes Riot page for a specific patch version
4. n8n workflow: activate + connect patch notes ingest + Discord webhook on new patch
5. Frontend: patch version badge + "stale" indicator when behind

---

### v1.2 MetaTFT Real-time Intelligence — SHIPPED ✅

**All features delivered (Phase 9):**
- META-01: `POST /api/ingest/metatft` — httpx scrape of `https://www.metatft.com/comps`
- META-02: MetaTFT Markdown transformer — comp tiers, carries, items → Vietnamese
- META-03: Space Gods data ingest — `ingest_tft_set17.py`, `scrape_set_overview.py`
- META-04: n8n `patch_monitor.json` daily trigger at 12:00 noon
- META-05: Frontend `CompCard` + `compParser.ts` → styled cards in MessageList

**Key files:**
- `apps/backend/app/routes/ingest.py` — `POST /api/ingest/metatft`
- `apps/backend/scripts/scrape_metatft.py` — MetaTFT scraper
- `apps/backend/scripts/scrape_set_overview.py` — Space Gods scraper
- `apps/backend/scripts/ingest_tft_set17.py` — Set 17 ingest script
- `apps/frontend/src/components/CompCard.tsx` — Comp card component
- `apps/frontend/src/utils/compParser.ts` — Markdown → comp data parser
- `n8n/workflows/patch_monitor.json` — n8n daily cron + Discord

---

### v1.3 Hardening & Polish — SHIPPED ✅

**All features verified (Phase 10):**
- HARD-01: Session switch loading spinner in `ChatShell.tsx` (lines 122-129)
- HARD-02: 60s timeout on `/api/chat` in `chat.ts` (lines 10-17)
- HARD-03: Pydantic `Field(ge=1, le=50)` on `top_k` in `models.py`
- HARD-04: CompCard component integrated in `MessageList.tsx` (Phase 9 META-05)
- HARD-05: Toast system (`useToast.ts` + `toast.tsx`) in `App.tsx`

**Root cause fixes applied:**
- Fix A: `useGpuStatus.ts` line 11 — `/health/gpu` → `/api/health/gpu`
- Fix B: `PatchStatus.tsx` line 19 — hardcoded URL → `/api/patch/status`

**Lesson learned:** Phase 10 was fully implemented but poorly documented. All 5 tasks existed in code. Only 2 path fixes were needed.

---

## Known Issues

### Security (Acknowledged)
- ⚠️ **RLS disabled on DB tables** — accepted risk for local-only deployment

### v1.1 Pre-Phase Warnings

| Phase | Pitfall | Mitigation |
|-------|---------|------------|
| All | n8n container can't reach `localhost:8000` | Use `http://backend:8000` in n8n workflows |
| All | n8n workflows `active: false` | Must be activated manually in n8n UI |
| Patch notes | Riot page structure changes | Graceful degradation + logging |
| Patch notes | CDN 403 on retired sets | Fallback to CommunityDragon |

---

## Session Continuity

### For Next Session

When starting new milestone work:
1. Run `/gsd-progress` to check current state
2. Start new-milestone via GSD workflow
3. Run health checks before starting:
   ```powershell
   ollama ps
   npx supabase status
   curl http://localhost:8000/api/health
   curl http://localhost:8000/api/health/gpu
   curl http://localhost:8000/api/patch/status
   ```

### Key Context for This Project

**What makes this project unique:**
- Local LLM (Ollama) + local vector DB (pgvector/HNSW) + local scraping
- 3 chat modes: Normal (no context), RAG (Obsidian + TFT data), Coach (strategic framing)
- MetaTFT daily data refresh via n8n cron
- CompCard renders meta comp data in styled UI
- Toast notifications for user feedback
- Session switch spinner prevents confusion during loading

**What was wrong with Phase 10 (and now fixed):**
- Phase 10 was planned with 5 new tasks to implement
- Codebase audit revealed ALL 5 tasks were already implemented
- Phase 10 was actually "done" — just the planning docs were wrong
- Two critical browser errors existed (GPU SyntaxError + PatchStatus CORS)
- Both errors caused by wrong API paths — both fixed

---
*State tracked: 2026-04-22*
*Last updated: 2026-04-23 at v1.3 Hardening & Polish ship*
