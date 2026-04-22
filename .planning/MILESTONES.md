# Milestones

## v1.0 MVP — SHIPPED 2026-04-22

**Date:** 2026-04-22
**Phases:** 7 (1-7)
**Plans:** 22+
**Smoke test:** 60/60 PASS

### Accomplishments

1. **Local-first AI copilot** — Ollama + FastAPI + React with full streaming chat
2. **3-mode chat** — Normal (free chat), RAG (grounded + cited), Coach (tactical advice)
3. **RAG pipeline** — Hybrid search (HNSW semantic + GIN full-text), Obsidian ingest, citation display
4. **TFT patch 17.1 data** — 32 chunks ingested from official Riot patch page + CommunityDragon
5. **Production polish** — TTL-LRU cache, GPU monitoring, 20-question smoke test eval
6. **Automation ready** — n8n workflows + Bearer token auth + patch monitoring

### Tech Decisions

- qwen3:1.7b (chat) + qwen3-embedding:4b (embedding) for 12GB VRAM compatibility
- Riot CDN + patch page scraping as data source (CDN blocks automated access)
- Embedding dimensions truncated from 2560 to 1024 (HNSW index limit)

### Archive

- [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md)
- [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md)
