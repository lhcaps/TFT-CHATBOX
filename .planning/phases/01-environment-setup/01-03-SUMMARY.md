# Phase 01-03 Summary: Docker Compose Setup

**Executed:** 2026-04-22
**Phase:** 01-03
**Type:** Infrastructure Configuration
**Status:** COMPLETED

---

## Overview

Created Docker Compose configuration for orchestrating backend, frontend, and n8n services with proper Windows compatibility for accessing host-native Ollama and Supabase.

---

## Files Created

| File | Purpose |
|------|---------|
| `infra/docker-compose.yml` | Main orchestration file with 3 services |
| `infra/.env.example` | Environment variable template for Docker |
| `apps/backend/.dockerignore` | Excludes unnecessary files from backend Docker build |
| `apps/frontend/.dockerignore` | Excludes unnecessary files from frontend Docker build |

---

## Key Decisions Implemented

| Decision | Implementation |
|----------|----------------|
| D-08: Only 3 services in compose | Backend, Frontend, n8n only |
| D-09: host.docker.internal for Ollama | `OLLAMA_BASE_URL: http://host.docker.internal:11434` |
| D-09: host.docker.internal for Supabase | `DATABASE_URL: postgresql://postgres:postgres@host.docker.internal:54322/postgres` |
| D-10: n8n pinned to 1.85 | `image: docker.n8n.io/n8nio/n8n:1.85` |

---

## Services Configured

### Backend (tft-backend)
- **Image:** Built from `../apps/backend/Dockerfile`
- **Ports:** 8000:8000
- **Dependencies:** Ollama (host.docker.internal:11434), Supabase (host.docker.internal:54322)
- **Volumes:** Source mount for hot reload, Obsidian vault (read-only)
- **Healthcheck:** `/health` endpoint, 30s interval

### Frontend (tft-frontend)
- **Image:** Built from `../apps/frontend/Dockerfile`
- **Ports:** 5173:5173
- **Volumes:** Source mount for hot reload
- **Healthcheck:** Root endpoint, 30s interval

### n8n (tft-n8n)
- **Image:** `docker.n8n.io/n8nio/n8n:1.85` (pinned)
- **Ports:** 5678:5678
- **Volumes:** `n8n_data` for persistence, workflows and files mounts
- **Timezone:** Asia/Ho_Chi_Minh
- **Healthcheck:** `/healthz` endpoint, 30s interval

---

## Windows Compatibility

All services include `extra_hosts` configuration:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This ensures `host.docker.internal` resolves correctly on Windows Docker Desktop.

---

## Verification

| Check | Result |
|-------|--------|
| docker-compose.yml exists | PASS |
| .env.example exists with Docker vars | PASS |
| .dockerignore files exist | PASS |
| n8n version 1.85 | PASS |
| host.docker.internal configured | PASS |

---

## Next Steps

- Phase 01-04: Create Dockerfile for backend
- Phase 01-05: Create Dockerfile for frontend

---

## Commit

```
a238f1c feat(phase 1): Add Docker Compose configuration for app services
```

---

*Summary generated: 2026-04-22*
