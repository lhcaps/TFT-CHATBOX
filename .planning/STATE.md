# STATE: TFT Local Copilot

**Project:** TFT Local Copilot
**Last updated:** 2026-04-22

---

## Project Reference

**Core Value:** A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem.

**Current Milestone:** v1.0 — MVP with Normal/RAG/Coach modes

---

## Current Position

**Active Phase:** Phase 3 - Frontend Chat (pending planning)

**Milestone Progress:** 2/7 phases complete

```
[x Phase 1 ] [x Phase 2  ] [ Phase 3 ] [ Phase 4 ] [ Phase 5 ] [ Phase 6 ] [ Phase 7 ]
    ✓           ✓          ○          ○          ○          ○          ○
```

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Requirements mapped | 35/35 | 100% coverage |
| Phases defined | 7 | Standard granularity |
| v1 requirements | 35 | All phases mapped |
| v2 requirements | 20+ | Deferred scope |

---

## Hardware Context

| Resource | Capacity | Usage |
|-----------|----------|-------|
| RAM | 64GB | Full system |
| VRAM | 16GB (RTX 4070 Ti SUPER) | Chat + Embedding models |
| Chat model | qwen3:8b | ~5.2GB VRAM |
| Embedding model | qwen3-embedding:4b | ~2.5GB VRAM |
| Optional | gemma3:12b | ~8.1GB VRAM (Coach mode) |

---

## Stack Summary

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 19 + Vite 6 + Tailwind 4 | Chat UI |
| Backend | FastAPI + Uvicorn | API orchestration |
| LLM | Ollama native (Windows) | qwen3:8b + qwen3-embedding:4b |
| Database | Supabase local CLI (pgvector/HNSW) | 1024-dim embeddings |
| Automation | n8n (Docker) | Scheduled workflows |
| Knowledge | Obsidian vault | Markdown notes |

---

## Key Decisions (Locked)

| Decision | Rationale | Status |
|----------|-----------|--------|
| Ollama native (not containerized) | GPU passthrough friction on Windows | Locked |
| 1024-dim embeddings | HNSW index limit 2000 dims | Locked |
| Supabase local CLI | Postgres + pgvector without Docker complexity | Locked |
| 3-mode chat (Normal/RAG/Coach) | TFT policy compliance | Locked |
| Obsidian as knowledge source only | Vault is Markdown/text only | Locked |
| n8n for automation | Cron ingest + webhook fan-out | Locked |
| SSE for streaming | Sufficient for one-way streaming | Locked |
| In-memory LRU cache | MVP scale doesn't need Redis | Locked |

---

## Accumulated Context

### Critical Constraints

1. **VRAM budget:** 16GB total — batch embedding capped at 16 chunks
2. **TFT policy:** No real-time overlay, no opponent scouting, suggest not dictate
3. **Windows native:** Ollama runs outside Docker for GPU access
4. **Port assignments:**
   - Ollama: 11434
   - Supabase Postgres: 54322
   - Supabase Studio: 54323
   - Backend: 8000
   - Frontend: 5173
   - n8n: 5678

### Phase Dependencies

```
Phase 1 (Foundation)
    │
    ├──► Phase 2 (Backend Core)
    │         │
    │         └──► Phase 3 (Frontend Chat)
    │                   │
    │                   └──► Phase 4 (RAG Foundation)
    │                             │
    │                             ├──► Phase 5 (TFT Static Data)
    │                             │         │
    │                             │         └──► Phase 6 (Automation)
    │                             │                   │
    │                             └──► ───────────────┘
    │                                           │
    │                                           ▼
    │                                    Phase 7 (Polish)
    │
    └──► ──────────────────────────────────────┘
```

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
| 4 | Wrong embedding dimensions | Always specify `dimensions: 1024` |
| 4 | Duplicate chunks on re-ingest | DELETE before INSERT |
| 5 | Coach TFT policy violations | No real-time, no scouting, suggest options |
| 6 | ngrok URL change | Script URL refresh on restart |
| 6 | Workflow not activated | Save AND activate toggle |

---

## Session Continuity

### For Next Session

When resuming work:
1. Run `/gsd-progress` to check current state
2. Start with lowest-numbered incomplete phase
3. Run health checks before starting:
   ```powershell
   ollama ps
   npx supabase status
   curl http://localhost:8000/health
   curl http://localhost:8000/sessions
   ```

### TODO

- [x] Initialize git repository
- [x] Create project directory structure (apps/backend, apps/frontend)
- [x] Set up .env file with all required environment variables
- [x] Enable Windows long path support
- [x] Configure git line endings (.gitattributes)
- [x] Install Ollama + pull models (qwen3:8b, qwen3-embedding:4b)
- [x] Install Supabase local CLI + start
- [x] Create database schema (4 tables, indexes, hybrid_search_chunks function)
- [x] Set up Docker Compose (backend + frontend + n8n)
- [x] Create healthcheck endpoint

---

## Research Files Available

| File | Purpose |
|------|---------|
| research/ARCHITECTURE.md | Component breakdown, data flow, build order |
| research/STACK.md | Technology recommendations, SSE patterns |
| research/PITFALLS.md | Common pitfalls per phase with mitigations |

---

*State tracked: 2026-04-22*
*Last updated: 2026-04-22*
