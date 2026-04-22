# STATE: TFT Local Copilot

**Project:** TFT Local Copilot
**Last updated:** 2026-04-22

---

## Project Reference

**Core Value:** A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem.

**Current Milestone:** v1.0 MVP — SHIPPED 2026-04-22 (60/60 smoke test PASS)

---

## Current Position

**Active Phase:** v1.0 COMPLETE — milestone archived

**Milestone Progress:** v1.0 MVP DONE

```
✅ v1.0 MVP — Phases 1-7 (shipped 2026-04-22)
```

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Requirements mapped | 35/35 | 100% coverage |
| Phases defined | 7 | Standard granularity |
| v1 requirements | 35 | All shipped |
| v2 requirements | 20+ | Deferred scope |
| Smoke test | 60/60 PASS | 20 questions × 3 modes |

---

## Hardware Context

| Resource | Capacity | Usage |
|-----------|----------|-------|
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
| Ollama native (not containerized) | GPU passthrough friction on Windows | Locked |
| 1024-dim embeddings | HNSW index limit 2000 dims, qwen3-embedding:4b truncates to 1024 | Locked |
| Supabase local CLI | Postgres + pgvector without Docker complexity | Locked |
| 3-mode chat (Normal/RAG/Coach) | TFT policy compliance | Locked |
| Obsidian as knowledge source only | Vault is Markdown/text only | Locked |
| n8n for automation | Cron ingest + webhook fan-out | Locked |
| SSE for streaming | Sufficient for one-way streaming | Locked |
| In-memory LRU cache | MVP scale doesn't need Redis | Locked |
| qwen3:1.7b chat model | Fits in 12GB VRAM alongside embedding model | Locked |
| Bearer token auth | Defense in Depth, future-proof | Locked |
| ngrok dropped | 100% local, no remote access needed | Locked |

---

## Accumulated Context

### Critical Constraints

1. **VRAM budget:** 12GB total — qwen3:1.7b (~1.4GB) + qwen3-embedding:4b (~2.5GB) + overhead
2. **TFT policy:** No real-time overlay, no opponent scouting, suggest not dictate
3. **Windows native:** Ollama runs outside Docker for GPU access
4. **Port assignments:**
   - Ollama: 11434
   - Supabase Postgres: 54322
   - Supabase Studio: 54323
   - Backend: 8000
   - Frontend: 5173
   - n8n: 5678

### Known Issues (Security Advisory)

- ⚠️ **RLS disabled on DB tables** (`chunks`, `messages`, `sessions`) — any user with anon key can read/write all rows. User must decide whether to enable RLS with policies.

### Known Pitfalls (Pre-Phase Warnings)

| Phase | Pitfall | Mitigation |
|-------|---------|------------|
| 1 | GPU not detected | Verify with `ollama ps` early |
| 1 | Path issues on Windows | Use `pathlib`, enable long paths |
| 1 | Supabase port conflicts | Check `npx supabase status` |
| 2 | CORS misconfigured | Explicit allow localhost:5173 |
| 2 | Ollama unreachable from Docker | Use `host.docker.internal` |
| 3 | SSE parsing errors | Buffer accumulation, split on `\n\n` |
| 3 | Abort doesn't work | Call `reader.cancel()`, release lock |
| 4 | Wrong embedding dimensions | Always truncate to 1024 dims (qwen3-embedding:4b creates 2560) |
| 4 | Duplicate chunks on re-ingest | DELETE before re-INSERT |
| 5 | Riot CDN 403 errors | Use User-Agent header, fallback to CommunityDragon + patch page scrape |
| 6 | Workflow not activated | Save AND activate toggle |

---

## Session Continuity

### For Next Session

When resuming work:
1. Run `/gsd-progress` to check current state
2. Start with planning v1.1 milestone
3. Run health checks before starting:
   ```powershell
   ollama ps
   npx supabase status
   curl http://localhost:8000/api/health
   ```

---

*State tracked: 2026-04-22*
*Last updated: 2026-04-22 after v1.0 milestone completion*
