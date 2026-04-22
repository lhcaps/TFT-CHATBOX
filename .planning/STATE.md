# STATE: TFT Local Copilot

**Project:** TFT Local Copilot
**Last updated:** 2026-04-22

---

## Project Reference

**Core Value:** A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem.

**Current Milestone:** v1.1 TFT Meta Mastery — planning in progress

---

## Current Position

**Active Phase:** Phase 8: Patch Meta Mastery (planned — ready to execute)

**Milestone Progress:**
```
✅ v1.0 MVP — Phases 1-7 (shipped 2026-04-22)
📋 v1.1 TFT Meta Mastery — planning pending
```

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| v1.0 Requirements mapped | 35/35 | 100% coverage |
| v1.0 Phases defined | 7 | All complete |
| v1.0 Smoke test | 60/60 PASS | 20 questions × 3 modes |
| v1.1 Phases | TBD | Planning pending |

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

### v1.1 Focus: TFT Meta Mastery

**Goal:** Automated TFT meta intelligence — backend tracks patch state in DB, n8n monitors Riot for new patches, auto-ingests patch notes + static data when available.

**Gap Analysis (from codebase audit):**
1. `patch_monitor.json` exists but `"active": false` — not running
2. `patch_state.py` reads from file `latest_version.txt`, not DB
3. No `patch_info` table in DB — no structured patch metadata storage
4. `scrape_patch17.py` is one-off script, not API-triggered
5. n8n `patch_monitor` only triggers `/ingest/tft-static`, NOT patch notes scraping
6. Frontend has no patch version display or staleness indicator

**What to build:**
1. DB `patch_info` table: stores current_patch, latest_available, last_checked, last_ingested
2. Backend API: `GET /api/patch/status` (returns current + latest + staleness)
3. Backend API: `POST /api/ingest/patch-notes` — scrapes Riot page for a specific patch version
4. n8n workflow: activate + connect patch notes ingest + Discord webhook on new patch
5. Frontend: patch version badge + "stale" indicator when behind

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

When resuming v1.1 work:
1. Run `/gsd-progress` to check current state
2. Continue from discuss-phase → plan-phase → execute-phase
3. Run health checks before starting:
   ```powershell
   ollama ps
   npx supabase status
   curl http://localhost:8000/api/health
   ```

---
*State tracked: 2026-04-22*
*Last updated: 2026-04-22 at v1.1 TFT Meta Mastery start*
