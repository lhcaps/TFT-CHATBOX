---
phase: 2
slug: backend-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-22
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `apps/backend/pytest.ini` (to be created) |
| **Quick run command** | `pytest tests/ -x -v` |
| **Full suite command** | `pytest tests/ --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_<module>.py -x`
- **After every plan wave:** Run `pytest tests/ --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|------------------|-------------|--------|
| 2-01-01 | 01 | 1 | BACK-01, BACK-03 | T-BACK-01 | Parameterized SQL | grep | `grep "pool.acquire" apps/backend/app/repositories/session.py` | ✅ | ⬜ pending |
| 2-01-02 | 01 | 1 | BACK-01, BACK-03 | T-BACK-02 | Parameterized SQL | grep | `grep "pool.acquire" apps/backend/app/repositories/message.py` | ✅ | ⬜ pending |
| 2-01-03 | 01 | 1 | BACK-03 | — | Config default | grep | `grep "chat_history_window.*=.*10" apps/backend/app/config.py` | ✅ | ⬜ pending |
| 2-02-01 | 02 | 1 | BACK-01, BACK-03 | T-BACK-04, T-BACK-05 | 404 for missing | unit | `pytest tests/test_sessions.py -x` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 2 | BACK-01, BACK-02, BACK-03 | T-BACK-06, T-BACK-07, T-BACK-08 | Input validation | unit | `pytest tests/test_chat_stream.py -x` | ❌ W0 | ⬜ pending |
| 2-04-01 | 04 | 3 | BACK-01, BACK-04 | T-BACK-09 | CORS allowlist | curl | `curl -I http://localhost:8000/health -H "Origin: http://localhost:5173"` | N/A | ⬜ pending |
| 2-04-02 | 04 | 3 | BACK-03 | — | Persistence | curl | Direct DB query | N/A | ⬜ pending |
| 2-04-03 | 04 | 3 | BACK-02 | — | SSE format | curl | SSE token/done/usage format check | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/backend/tests/` directory — test files for all repositories and routes
- [ ] `apps/backend/tests/conftest.py` — shared fixtures (asyncpg pool, test client)
- [ ] `apps/backend/tests/test_sessions.py` — covers BACK-01 session CRUD
- [ ] `apps/backend/tests/test_chat_stream.py` — covers BACK-02 SSE streaming
- [ ] `apps/backend/tests/test_chat_nonstream.py` — covers BACK-02 non-streaming
- [ ] `apps/backend/tests/test_history_window.py` — covers history window logic
- [ ] `apps/backend/pytest.ini` — pytest-asyncio configuration: `asyncio_mode = auto`
- [ ] Install: `pip install pytest pytest-asyncio httpx`

*All gaps are Wave 0 — test infrastructure needed before implementation starts*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SSE token event format `{"token": "..."}` | BACK-02 | Requires running backend + curl inspection | `curl -N .../chat ...` then verify event lines match format |
| CORS preflight allows localhost:5173 | BACK-04 | Browser CORS headers can't be tested in unit tests | `curl -v -X OPTIONS ... -H "Origin: http://localhost:5173"` |
| Messages persist to DB across restarts | BACK-03 | Integration test requires running Postgres | Direct `psql` query after backend restart |
| Ollama streaming from native Windows | BACK-02 | Requires live Ollama + GPU | `curl -N -X POST .../chat` — watch tokens appear |

*All phase behaviors have automated or manual verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
