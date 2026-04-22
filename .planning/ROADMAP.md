# ROADMAP: TFT Local Copilot

**Project:** TFT Local Copilot
**Created:** 2026-04-22
**Granularity:** standard
**Parallelization:** enabled (yolo mode)

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-04-22) — 60/60 smoke test PASS
- 📋 **v1.1 TFT Meta Mastery** — planning pending

---

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) — SHIPPED 2026-04-22</summary>

- [x] Phase 1: Environment Setup (5/5 plans) — completed 2026-04-22
- [x] Phase 2: Backend Core (4/4 plans) — completed 2026-04-22
- [x] Phase 3: Frontend Chat (complete) — completed 2026-04-22
- [x] Phase 4: RAG Foundation (3/3 plans) — completed 2026-04-22
- [x] Phase 5: TFT Static Data (4/4 plans) — completed 2026-04-22
- [x] Phase 6: Automation (4/4 plans) — completed 2026-04-22
- [x] Phase 7: Polish & Smoke Test (4/4 plans) — completed 2026-04-22

**Smoke Test:** 60/60 PASS — 20 questions × 3 modes (Normal/RAG/Coach)

Full details: [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md)

</details>

### 📋 v1.1 TFT Meta Mastery (Planned)

**Goal:** Automated TFT meta intelligence — backend tracks patch state in DB, n8n monitors Riot for new patches, auto-ingests patch notes + static data when available.

**Requirements:**
- PATCH-01: Patch state table in DB (current_patch, latest_available, last_checked, last_ingested)
- PATCH-02: Backend patch status API (GET /api/patch/status → current, latest, staleness)
- PATCH-03: Auto-scrape patch notes API (POST /api/ingest/patch-notes → scrape + ingest)
- PATCH-04: n8n workflow activation + full patch monitoring (static + notes + Discord webhook)
- PATCH-05: Frontend patch version display + staleness badge

**Depends on:** Phase 6 (Automation)

**Success criteria:**
1. `GET /api/patch/status` returns `{current, latest, is_stale, last_checked, last_ingested}` from DB
2. `POST /api/ingest/patch-notes?patch=X.Y` scrapes Riot page + ingests chunks into DB
3. n8n `patch_monitor` workflow is `active: true` and triggers both static data + patch notes ingest
4. Frontend shows patch version badge with staleness state

**Gaps from v1.0:**
- `patch_monitor.json` exists but `"active": false`
- `patch_state.py` reads from file, not DB — no structured metadata
- No `patch_notes` ingestion endpoint (scrape_patch17.py is one-off script)
- Frontend has no patch/staleness display

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|--------------|--------|-----------|
| 1. Environment Setup | v1.0 | 5/5 | Complete | 2026-04-22 |
| 2. Backend Core | v1.0 | 4/4 | Complete | 2026-04-22 |
| 3. Frontend Chat | v1.0 | N/N | Complete | 2026-04-22 |
| 4. RAG Foundation | v1.0 | 3/3 | Complete | 2026-04-22 |
| 5. TFT Static Data | v1.0 | 4/4 | Complete | 2026-04-22 |
| 6. Automation | v1.0 | 4/4 | Complete | 2026-04-22 |
| 7. Polish & Smoke Test | v1.0 | 4/4 | Complete | 2026-04-22 |
| 8. Patch Meta Mastery | v1.1 | 4/4 | Planned | — |

---

## v2 Requirements (Deferred)

> Note: PATCH-* requirements below are being addressed in **v1.1 TFT Meta Mastery**.

### Patch Automation (v1.1 — in progress)
- PATCH-01: Patch state table in DB (current_patch, latest_available, last_checked, last_ingested)
- PATCH-02: Backend patch status API (GET /api/patch/status)
- PATCH-03: Auto-scrape patch notes API (POST /api/ingest/patch-notes)
- PATCH-04: n8n workflow activation + full patch monitoring + Discord webhook
- PATCH-05: Frontend patch version display + staleness badge
- RAG-08: Inline citation cards with hover/tap source snippets
- RAG-09: Streaming citation reveal alongside tokens
- RAG-10: Retrieval debug panel showing chunks, scores, sources
- RAG-11: Heuristic reranking: patch/season priority before cosine score
- RAG-12: Obsidian file watcher for real-time reactive sync

### Coach Mode Enhancements
- PROMPT-04: Visual line-of-play cards with icons (econ, tempo, board cap)
- PROMPT-05: Pivot fallback chain in every coach response
- PROMPT-06: In-game scenario presets (fast 8 roll, hyperoll open, 1-star holding)
- PROMPT-07: Coach persona customization (aggressive, safe, pivoting)

### Session Features
- SESS-01: Session auto-naming from first message
- SESS-02: Session search by keyword
- SESS-03: Session export as Markdown to Obsidian
- SESS-04: Cross-session memory from past conversations

### Model Upgrades
- MODEL-01: gemma3:12b for Coach mode, qwen3:8b for Normal/RAG
- MODEL-02: Query embedding cache (30-min TTL)

### Eval / Observability
- EVAL-01: Smoke test suite with scoring
- EVAL-02: Retrieval quality metrics (recall@K)
- EVAL-03: Structured logging for every request

---

## TFT Policy Compliance Notes

All phases comply with Riot TFT policy:
- **No real-time data:** Never build overlay, screen capture, or opponent scouting features
- **No game state reading:** Coach mode suggestions based on user's stated context only
- **Suggest, don't dictate:** Coach responses frame recommendations as options with trade-offs
- **Local-only:** All data stays on user's machine — no external API calls except Riot Data Dragon (static)
- **Unofficial tool:** Clearly disclaim no affiliation with Riot Games

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time opponent scouting / board scanning | Violates Riot TFT policy |
| In-game overlay or HUD | Violates TFT policy; dictates decisions |
| Automated "best action" button or macro | Removes player agency |
| Cloud API dependencies | Must remain fully local |
| Auth / user management | Single local user, no multi-user need |
| Non-Windows targets | MVP is Windows-only |
| WebSocket instead of SSE | SSE is sufficient for streaming |
| Redis or distributed cache | In-memory LRU sufficient for MVP |
| Cross-encoder reranking | Heuristic reranking is good enough for MVP |

---

## Archive

- [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md) — Full v1.0 phase details
- [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md) — All 35 v1 requirements (shipped)

---

*Last updated: 2026-04-22*
*Completed: v1.0 MVP — Phases 1-7 (shipped 2026-04-22)*
