---
phase: 6
slug: automation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-22
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

Phase 6 is primarily a configuration + n8n workflow phase. There is no Python test framework for n8n workflows themselves. Verification is:

| Verification Type | Method | Command |
|-------------------|--------|---------|
| Backend auth | Manual curl | `curl -H "Authorization: Bearer <key>" http://localhost:8000/api/ingest/obsidian` |
| Backend state endpoint | Manual curl | `curl http://localhost:8000/api/patch/current` |
| n8n workflow JSON | Grep + JSON lint | `grep` + `python -c "import json; json.load(open(...))"` |
| Docker Compose | Docker inspect | `docker compose config` |
| n8n credential | Manual UI | n8n Settings → Credentials |

**Quick run:** No automated test suite. Use `grep` commands from each plan's `<verify>` block.
**Full suite:** Manual verification per plan's `<verification>` block.
**Estimated runtime:** N/A — no automated tests.

---

## Sampling Rate

- **After every task commit:** Run the `grep` commands from the plan's `<verify>` block
- **After every plan wave:** Run the plan's `<verification>` section
- **Before `$gsd-verify-work`:** All grep checks pass + manual n8n UI verification
- **Max feedback latency:** Immediate (grep output)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | AUTO-02 | T-06-40 | Bearer token validated on ingest; 401 on missing/invalid | grep + curl | `grep "verify_api_key" apps/backend/app/routes/ingest.py` | ✅ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | AUTO-02 | — | N/A | grep | `grep "api/patch/current" apps/backend/app/main.py` | ✅ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | AUTO-02 | — | N/A | grep | `grep "api_secret_key" apps/backend/app/config.py` | ✅ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | AUTO-02 | T-06-41 | Auth middleware applied to ALL ingest endpoints | grep | `grep "Depends(verify_api_key)" apps/backend/app/routes/ingest.py` | ✅ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | AUTO-04 | T-06-10 | API_SECRET_KEY in .env, not hardcoded | grep | `grep "GENERIC_TIMEZONE" infra/docker-compose.yml` | ✅ W0 | ⬜ pending |
| 06-02-02 | 02 | 1 | AUTO-04 | T-06-10 | API_SECRET_KEY in docker-compose env var | grep | `grep "API_SECRET_KEY" infra/docker-compose.yml` | ✅ W0 | ⬜ pending |
| 06-03-01 | 03 | 1 | AUTO-01 | T-06-20 | Bearer token in n8n credential, not JSON | grep | `grep "tftBackendApi" n8n/workflows/obsidian_ingest.json` | ✅ W0 | ⬜ pending |
| 06-03-02 | 03 | 1 | AUTO-01 | T-06-20 | Manual trigger (no cron); correct URL | grep | `grep "webhook" n8n/workflows/obsidian_ingest.json` | ✅ W0 | ⬜ pending |
| 06-04-01 | 04 | 2 | AUTO-02 | T-06-30 | Discord URL from credential, not env var | grep | `grep "credentials.discordWebhook" n8n/workflows/patch_monitor.json` | ✅ W0 | ⬜ pending |
| 06-04-02 | 04 | 2 | AUTO-02 | T-06-31 | Discord webhook in encrypted n8n credential | manual | n8n Settings → Credentials → discordWebhook exists | manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] No Wave 0 stub files needed — all verification is grep-based or manual n8n UI
- [ ] Backend Python changes are covered by existing backend health check (Phase 2)

*Phase 6 has no automated test suite. All verification is grep commands + manual n8n UI checks.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bearer token correctly rejects 401 on missing/invalid header | AUTO-02 | Requires live backend + curl command | 1. Start backend: `cd apps/backend && uvicorn app.main:app` 2. Missing auth: `curl -X POST http://localhost:8000/api/ingest/obsidian` → expect 401 3. Invalid auth: `curl -H "Authorization: Bearer wrong" http://localhost:8000/api/ingest/obsidian` → expect 401 4. Valid auth: `curl -H "Authorization: Bearer <API_SECRET_KEY>" http://localhost:8000/api/ingest/obsidian` → expect 200 or 422 (not 401) |
| Patch state endpoint returns correct JSON | AUTO-02 | Requires live backend + file cache | 1. Ensure `~/.tft-copilot/cache/latest_version.txt` exists with a version 2. `curl http://localhost:8000/api/patch/current` → expect `{"version": "...", "cached_at": "..."}` |
| n8n credentials created correctly | AUTO-01, AUTO-02 | Credentials are stored encrypted in n8n DB | 1. Open http://localhost:5678 → Settings → Credentials 2. Verify `tftBackendApi` exists with type "Header Auth" 3. Verify `discordWebhook` exists with full Discord URL |
| n8n workflow activates successfully | AUTO-01, AUTO-02 | Requires live n8n + Docker | 1. Open http://localhost:5678 → Workflows 2. Open "Obsidian Ingest Workflow" → toggle Activate 3. Open "Patch Monitor Workflow" → toggle Activate 4. Test: click Execute on Obsidian workflow → should POST to backend |

---

## Validation Sign-Off

- [ ] All tasks have grep-based automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5 seconds (grep is instant)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

