---
phase: "13-smart-chat-engine"
plan: "04"
subsystem: "backend"
tags: ["query-router", "knowledge-graph", "smart-routing", "smart-chat"]
key-files:
  created:
    - "apps/backend/app/services/router.py"
  modified:
    - "apps/backend/app/routes/graph.py"
    - "apps/backend/app/routes/chat.py"
metrics:
  router_patterns: 24
  sources_supported: 3
  graph_endpoints_added: 1
---

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | QueryRouter class with classify_query() + 24 regex patterns for graph/RAG/MetaTFT routing | `a22f852` |
| 2 | GET /api/graph/suggest endpoint with entity detection and contextual suggestions | `a22f852` |
| 3 | QueryRouter wired into chat endpoint, graph context injected into build_messages() | `a22f852` |

## Deviations

- Router normalize() duplicated in router.py to avoid circular import from routes/graph.py (acceptable — separate module)
- No other deviations.

## Self-Check

- [x] QueryRouter: `grep "class QueryRouter" apps/backend/app/services/router.py` returns 1
- [x] /api/graph/suggest: `grep "@router.get(\"/suggest\")" apps/backend/app/routes/graph.py` returns 1
- [x] Chat wiring: `grep "QueryRouter" apps/backend/app/routes/chat.py` returns 1
- [x] No modifications to shared orchestrator artifacts
