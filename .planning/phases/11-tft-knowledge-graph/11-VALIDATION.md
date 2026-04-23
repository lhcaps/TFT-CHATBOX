---
phase: 11
slug: tft-knowledge-graph
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-23
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|---------|-------|
| **Framework** | pytest |
| **Config file** | apps/backend/pytest.ini (or pyproject.toml) |
| **Quick run command** | `pytest apps/backend/tests/test_graph.py -x -v --tb=short` |
| **Full suite command** | `pytest apps/backend/tests/test_graph.py -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest apps/backend/tests/test_graph.py -x -v --tb=short`
- **After every plan wave:** Run `pytest apps/backend/tests/test_graph.py -v`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | KNOW-01 | T-11-01 | N/A (data only) | unit | `pytest apps/backend/tests/test_graph.py::test_graph_loads_all_node_types -x` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | KNOW-01 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_graph_minimum_node_counts -x` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | KNOW-01 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_node_attributes -x` | ❌ W0 | ⬜ pending |
| 11-01-04 | 01 | 1 | KNOW-01 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_has_trait_edges -x` | ❌ W0 | ⬜ pending |
| 11-01-05 | 01 | 1 | KNOW-01 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_builds_from_edges -x` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | KNOW-02 | T-11-01 | Input validation on entity name | integration | `pytest apps/backend/tests/test_graph.py::test_query_returns_neighbors -x` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | KNOW-02 | — | N/A | integration | `pytest apps/backend/tests/test_graph.py::test_neighbors_filter_by_type -x` | ❌ W0 | ⬜ pending |
| 11-02-03 | 02 | 1 | KNOW-02 | T-11-01 | 404 with suggestions on missing entity | integration | `pytest apps/backend/tests/test_graph.py::test_missing_entity_404 -x` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 1 | KNOW-03 | — | N/A | integration | `pytest apps/backend/tests/test_graph.py::test_reload_rebuilds_graph -x` | ❌ W0 | ⬜ pending |
| 11-03-02 | 03 | 1 | KNOW-03 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_reload_clears_cache -x` | ❌ W0 | ⬜ pending |
| 11-04-01 | 04 | 1 | KNOW-04 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_circular_references -x` | ❌ W0 | ⬜ pending |
| 11-04-02 | 04 | 1 | KNOW-04 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_empty_traits -x` | ❌ W0 | ⬜ pending |
| 11-04-03 | 04 | 1 | KNOW-04 | — | N/A | unit | `pytest apps/backend/tests/test_graph.py::test_depth_limited_traversal -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/backend/requirements.txt` — add `networkx` dependency
- [ ] `apps/backend/tests/test_graph.py` — stubs for all KNOW-04 tests
- [ ] `apps/backend/tests/conftest.py` — shared fixtures (sample JSON fixture data)
- [ ] `apps/backend/tests/fixtures/` — subset of verified JSON files for unit testing

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Graph loads on first API query (lazy-load behavior) | KNOW-01 | Requires first-query timing, hard to unit test | Start backend, send `GET /api/graph/neighbors/briar`, verify response time <2s |
| API integrates with existing router in app.py | KNOW-02 | Router registration can't be unit tested | Verify router included in `app.include_router()` call |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
