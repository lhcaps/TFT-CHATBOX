# Phase 6: Automation — Pattern Map

**Mapped:** 2026-04-22
**Files analyzed:** 8 source files + phase context
**Analogs found:** 7 / 8

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `apps/backend/app/middleware/auth.py` | middleware | request-response | None (new) | — |
| `apps/backend/app/routes/patch_state.py` | controller | request-response | `apps/backend/app/routes/health.py` | exact |
| `apps/backend/app/routes/ingest.py` | controller | request-response | `apps/backend/app/routes/ingest.py` | exact |
| `apps/backend/app/config.py` | config | — | `apps/backend/app/config.py` | exact |
| `infra/docker-compose.yml` | config | — | `infra/docker-compose.yml` | exact |
| `n8n/workflows/obsidian_ingest.json` | workflow | request-response | `n8n/workflows/obsidian_ingest.json` | exact |
| `n8n/workflows/patch_monitor.json` | workflow | request-response | `n8n/workflows/patch_check.json` | exact |
| `infra/.env.example` | config | — | `infra/.env.example` | exact |

---

## Pattern Assignments

### `apps/backend/app/middleware/auth.py` (CREATE — middleware, request-response)

**Role:** FastAPI dependency for Bearer token validation
**Match:** No existing analog — new file

**Pattern: FastAPI `Depends` auth dependency**

The backend uses FastAPI's dependency injection pattern. See `apps/backend/app/routes/sessions.py` for how `async def _session_repo()` is used as a dependency pattern.

**Core pattern (reference from `sessions.py` lines 13-15):**

```python
async def _session_repo() -> SessionRepository:
    pool = await get_pool()
    return SessionRepository(pool)
```

The auth middleware should follow the same `async def verify_api_key()` pattern, returning a value or raising `HTTPException`.

**Key implementation details from CONTEXT.md D-10, D-11:**
- Read `Authorization: Bearer <token>` header
- Compare against `settings.api_secret_key`
- Return `401 Unauthorized` on mismatch or missing header
- Use `from fastapi import Depends, HTTPException, Header` imports

**Skeleton:**

```python
from __future__ import annotations

from fastapi import Depends, HTTPException, Header

from app.config import settings


async def verify_api_key(authorization: str = Header(...)) -> str:
    """Validate Bearer token and return the token on success."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[len("Bearer ") :]
    if token != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
```

**Usage in routes** (reference from `apps/backend/app/routes/ingest.py` lines 7-9):

```python
from fastapi import APIRouter, HTTPException
# Add Depends import:
from fastapi import Depends
# Import the dependency:
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/obsidian")
async def ingest_obsidian(_: str = Depends(verify_api_key)) -> dict:
    # ... existing body
```

---

### `apps/backend/app/routes/patch_state.py` (CREATE — controller, request-response)

**Role:** Returns current cached patch version from `~/.tft-copilot/cache/latest_version.txt`
**Analog:** `apps/backend/app/routes/health.py` (exact role + data flow match)

**Imports pattern** (`health.py` lines 1-12):

```python
"""Health check endpoint."""
from __future__ import annotations

import logging

import asyncpg
import httpx
from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])
```

**Core endpoint pattern** (`health.py` lines 17-18):

```python
@router.get("/health")
async def health_check() -> dict[str, str]:
```

**State read pattern from `ingest_tft_static.py` lines 164-169:**

```python
async def get_cached_version() -> str | None:
    """Get the latest cached version from the marker file."""
    marker = _get_cached_version_marker()
    if marker is None:
        return None
    return marker.read_text(encoding="utf-8").strip()
```

Marker file path: `Path(settings.tft_cache_dir) / "latest_version.txt"` (line 175)

**Combined pattern — `patch_state.py` should:**

```python
"""Patch state endpoint — returns currently ingested TFT patch version."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/patch", tags=["patch"])


@router.get("/current")
async def get_current_patch() -> dict:
    """Return the currently cached TFT patch version.
    
    Reads from ~/.tft-copilot/cache/latest_version.txt.
    Returns {"version": "17.1"} or {"version": null} if not yet ingested.
    """
    from pathlib import Path
    
    marker = Path(settings.tft_cache_dir) / "latest_version.txt"
    if not marker.exists():
        return {"version": None}
    
    return {"version": marker.read_text(encoding="utf-8").strip()}
```

**Router registration** (reference from `apps/backend/app/main.py` line 50):

```python
from app.routes import health, sessions, chat, search, ingest, patch_state  # noqa: E402, F401

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(ingest.router)
app.include_router(patch_state.router)  # ADD THIS
```

---

### `apps/backend/app/routes/ingest.py` (MODIFY — controller, request-response)

**Change:** Add `Depends(verify_api_key)` to `POST /ingest/obsidian` and `POST /ingest/tft-static`
**Closest analog:** Same file (existing endpoint pattern)

**Current endpoint signature** (`ingest.py` lines 14-15):

```python
@router.post("/obsidian")
async def ingest_obsidian() -> dict:
```

**Modified signature:**

```python
from fastapi import Depends
from app.middleware.auth import verify_api_key

@router.post("/obsidian")
async def ingest_obsidian(_: str = Depends(verify_api_key)) -> dict:
```

**Current endpoint signature** (`ingest.py` lines 32-33):

```python
@router.post("/tft-static")
async def ingest_tft_static_route(patch: str | None = None) -> dict:
```

**Modified signature:**

```python
@router.post("/tft-static")
async def ingest_tft_static_route(
    patch: str | None = None,
    _: str = Depends(verify_api_key),
) -> dict:
```

**Note:** `GET /ingest/tft-static/version` remains unauthenticated (public read-only).

---

### `apps/backend/app/config.py` (MODIFY — config)

**Change:** Add `api_secret_key: str` from `API_SECRET_KEY` env var
**Closest analog:** Same file (existing settings pattern)

**Current pattern** (`config.py` lines 9-16):

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

**Add after existing settings** (append before `settings = Settings()` at line 64):

```python
    # API Auth
    api_secret_key: str = ""
```

**Pattern for env var loading** — pydantic_settings automatically reads `API_SECRET_KEY` env var into `api_secret_key` field. Default empty string ensures startup fails fast if not configured.

---

### `infra/docker-compose.yml` (MODIFY — config)

**Change:** Add `GENERIC_TIMEZONE=Asia/Ho_Chi_Minh` and `N8N_PROXY_HOPS=1` to n8n service
**Closest analog:** Same file (existing n8n service definition)

**Current n8n service** (`docker-compose.yml` lines 28-40):

```yaml
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=tft-copilot
      - N8N_HOST=localhost
      - N8N_PROTOCOL=http
    volumes:
      - ../n8n/workflows:/home/node/.n8n/workflows
      - ../n8n/local-files:/files
```

**Modified n8n service:**

```yaml
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=tft-copilot
      - N8N_HOST=localhost
      - N8N_PROTOCOL=http
      - GENERIC_TIMEZONE=Asia/Ho_Chi_Minh
      - N8N_PROXY_HOPS=1
    volumes:
      - ../n8n/workflows:/home/node/.n8n/workflows
      - ../n8n/local-files:/files
```

**Pattern:** Environment variables are flat `- KEY=value` lines under the `environment:` block.

---

### `n8n/workflows/obsidian_ingest.json` (MODIFY — workflow, request-response)

**Changes:**
1. Convert from `cron` trigger to `webhook` trigger (manual trigger)
2. Fix URL from `/ingest` → `/api/ingest/obsidian`
3. Add Bearer auth header from `tftBackendApi` credential
4. Update workflow name and id

**Closest analog:** Same file (existing workflow structure)
**Existing bug to fix:** URL is currently `http://backend:8000/ingest` (wrong path, no auth)

**Current trigger node** (`obsidian_ingest.json` lines 4-18):

```json
{
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "cronExpression",
          "expression": "0 2 * * *"
        }
      ]
    }
  },
  "name": "Scheduled Trigger",
  "type": "n8n-nodes-base.cron",
  "typeVersion": 1,
  "position": [250, 300]
}
```

**New webhook trigger node:**

```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "obsidian-ingest",
    "responseMode": "onReceived",
    "options": {}
  },
  "name": "Manual Webhook",
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 1,
  "position": [250, 300]
}
```

**Current HTTP Request node** (`obsidian_ingest.json` lines 20-29):

```json
{
  "parameters": {
    "url": "http://backend:8000/ingest",
    "method": "POST"
  },
  "name": "Trigger Backend Ingest",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4,
  "position": [500, 300]
}
```

**New HTTP Request node with Bearer auth:**

```json
{
  "parameters": {
    "url": "http://backend:8000/api/ingest/obsidian",
    "method": "POST",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Authorization",
          "value": "Bearer = Cre"
        }
      ]
    }
  },
  "credentials": {
    "httpHeaderAuth": "tftBackendApi"
  },
  "name": "Trigger Backend Ingest",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4,
  "position": [500, 300]
}
```

**Pattern note:** n8n credentials are referenced by name in the `credentials` field. The credential (`tftBackendApi`) must be created in n8n UI with type "Header Auth".

---

### `n8n/workflows/patch_monitor.json` (CREATE — workflow, event-driven + request-response)

**Role:** Scheduled (6h cron) → Riot versions.json → backend `/api/patch/current` → compare → conditional POST ingest → Discord on failure
**Closest analog:** `n8n/workflows/patch_check.json` (existing structure, same n8n JSON format)

**Reference: n8n workflow JSON structure** (`patch_check.json` lines 1-39):

```json
{
  "name": "Patch Check Workflow",
  "nodes": [
    {
      "parameters": { /* cron or webhook trigger */ },
      "name": "Scheduled Trigger",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "http://backend:8000/health",
        "method": "GET"
      },
      "name": "Health Check",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [500, 300]
    }
  ],
  "connections": {
    "Scheduled Trigger": {
      "main": [[{"node": "Health Check", "type": "main", "index": 0}]]
    }
  },
  "active": false,
  "settings": {},
  "id": "patch-check"
}
```

**Workflow nodes required:**

1. **Trigger:** Cron `0 */6 * * *` (every 6 hours)
2. **HTTP GET Riot:** `https://ddragon.leagueoflegends.com/api/versions.json` → extract first element as `latestVersion`
3. **HTTP GET Backend:** `http://backend:8000/api/patch/current` → extract `$.version` as `cachedVersion`
4. **IF Node:** Compare `latestVersion !== cachedVersion`
   - **True branch:** HTTP POST `http://backend:8000/api/ingest/tft-static` with Bearer auth → Discord notification on failure
   - **False branch:** Stop (log: "No new patch detected")
5. **Discord Notify:** HTTP POST Discord webhook URL with embed (red, title "TFT Patch Ingest Failed")

**Discord embed format** (from CONTEXT.md D-14):

```json
{
  "content": "",
  "embeds": [{
    "title": "TFT Patch Ingest Failed",
    "color": 15158332,
    "fields": [
      {"name": "Patch", "value": "{{ $json.version }}", "inline": true},
      {"name": "Error", "value": "{{ $json.error }}", "inline": false},
      {"name": "Action", "value": "Manual intervention required", "inline": false}
    ],
    "timestamp": "{{ $now }}"
  }]
}
```

**Pattern: Error handling** — n8n IF node routes true/false. Use "Error Trigger" node or handle HTTP errors via node-level error output.

---

### `infra/.env.example` (MODIFY — config)

**Changes:**
1. Add `API_SECRET_KEY=<your-secret-here>`
2. Add `DISCORD_WEBHOOK_URL=<your-webhook-url>`

**Closest analog:** Same file (existing env var pattern)

**Current file** (`infra/.env.example` lines 1-32):

```bash
# n8n Configuration
WEBHOOK_URL=http://localhost:5678/
N8N_PROXY_HOPS=1
GENERIC_TIMEZONE=Asia/Ho_Chi_Minh
TZ=Asia/Ho_Chi_Minh
```

**Add after n8n Configuration section:**

```bash
# API Auth (shared secret between n8n and backend)
API_SECRET_KEY=<your-secret-here>

# Discord Webhook (for automation notifications)
DISCORD_WEBHOOK_URL=<your-webhook-url>
```

**Pattern:** New env vars added as flat key=value pairs. Use same format as existing entries.

---

## Shared Patterns

### Authentication: FastAPI `Depends` Dependency
**Source:** `apps/backend/app/routes/sessions.py` (lines 13-15 for dependency pattern), `apps/backend/app/routes/ingest.py` (target for modification)
**Apply to:** `apps/backend/app/middleware/auth.py` (new file)
**Pattern:**

```python
async def verify_api_key(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[len("Bearer ") :]
    if token != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
```

### State Management: Disk-based version marker
**Source:** `apps/backend/scripts/ingest_tft_static.py` (lines 156-176)
**Apply to:** `apps/backend/app/routes/patch_state.py`
**Pattern:**

```python
marker = Path(settings.tft_cache_dir) / "latest_version.txt"
if not marker.exists():
    return {"version": None}
return {"version": marker.read_text(encoding="utf-8").strip()}
```

### n8n HTTP Request with Bearer Auth
**Source:** `n8n/workflows/obsidian_ingest.json` (current broken version — fix URL + add auth)
**Apply to:** `n8n/workflows/obsidian_ingest.json` (modify), `n8n/workflows/patch_monitor.json` (create)
**Pattern:**

```json
{
  "parameters": {
    "url": "http://backend:8000/api/ingest/obsidian",
    "method": "POST",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [{"name": "Authorization", "value": "Bearer = Cre"}]
    }
  },
  "credentials": {"httpHeaderAuth": "tftBackendApi"}
}
```

### n8n Cron Trigger
**Source:** `n8n/workflows/patch_check.json` (lines 4-13)
**Apply to:** `n8n/workflows/patch_monitor.json`
**Pattern:**

```json
{
  "parameters": {
    "rule": {
      "interval": [{
        "field": "cronExpression",
        "expression": "0 */6 * * *"
      }]
    }
  },
  "name": "Scheduled Trigger",
  "type": "n8n-nodes-base.cron",
  "typeVersion": 1
}
```

### Config: pydantic_settings environment variable
**Source:** `apps/backend/app/config.py` (lines 9-64)
**Apply to:** `apps/backend/app/config.py` (modify)
**Pattern:** Field name `api_secret_key` auto-maps to `API_SECRET_KEY` env var via pydantic.

### Docker Compose n8n environment variables
**Source:** `infra/docker-compose.yml` (lines 32-37)
**Apply to:** `infra/docker-compose.yml` (modify)
**Pattern:** Flat `- KEY=value` lines under `environment:` key.

---

## No Analog Found

Files with no close match (planner should use RESEARCH.md / CONTEXT.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `apps/backend/app/middleware/auth.py` | middleware | request-response | No existing auth middleware in project — implement as FastAPI `Depends` |

---

## n8n Credentials Reference

Based on CONTEXT.md D-08, D-11:

| Credential Name | Type | Used By | Store In |
|-----------------|------|---------|----------|
| `tftBackendApi` | Header Auth | obsidian_ingest.json, patch_monitor.json | n8n UI (encrypted) |
| `discordWebhook` | Generic Credential (URL) | patch_monitor.json | n8n UI (encrypted) |

**Credential creation steps** (deferred to n8n UI — not scriptable in JSON):
1. n8n UI → Settings → Credentials → Add → "Header Auth" → name `tftBackendApi` → header name `Authorization`, prefix `Bearer `
2. n8n UI → Settings → Credentials → Add → "Custom Credentials" → name `discordWebhook` → set URL field

---

## Metadata

**Analog search scope:**
- `apps/backend/app/routes/` — 4 files (health, sessions, chat, ingest, search)
- `apps/backend/app/` — config.py, main.py
- `apps/backend/scripts/` — ingest_tft_static.py, ingest_obsidian.py
- `infra/` — docker-compose.yml, .env.example
- `n8n/workflows/` — patch_check.json, obsidian_ingest.json

**Files scanned:** 12 source files
**Pattern extraction date:** 2026-04-22

---

*Pattern mapping complete. Planner can reference analog files and excerpts above when writing PLAN.md action items.*
