# Phase 6: Automation - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Build two n8n automation workflows and a backend state endpoint: (1) Obsidian manual-trigger webhook, (2) Patch monitor that detects new TFT patches via Riot versions.json, checks backend state, and triggers ingest with Discord/Email notification on CDN failure. API Key auth protects all ingest endpoints.

**Scope:** n8n workflows (Obsidian ingest, patch monitor), backend state endpoint (`/api/patch/current`), Bearer token auth on ingest endpoints, notification on ingest failure, Docker Compose n8n timezone env.
**Out of scope:** ngrok (bỏ hoàn toàn), scheduled Obsidian ingest (manual trigger only), CommunityDragon automatic fallback.
</domain>

<decisions>
## Implementation Decisions

### Obsidian Ingest: Manual Trigger (D-01 to D-03)
- **D-01:** Obsidian ingest là **manual webhook trigger** — không chạy lịch cố định, không theo dõi file ngầm. User trigger bằng lệnh CLI hoặc nút trong n8n UI.
- **D-02:** n8n workflow tạo một **webhook node** (POST endpoint). Backend gọi webhook này khi user muốn ingest, HOẶC user trigger trực tiếp từ n8n UI.
- **D-03:** Workflow chạy: Manual Webhook Trigger → HTTP POST `http://backend:8000/api/ingest/obsidian` (với auth header). Không có schedule node.

### Patch Monitor Logic (D-04 to D-08)
- **D-04:** n8n workflow patch monitor: Schedule Trigger every 6 hours → check Riot `versions.json` → gọi backend `/api/patch/current` → so sánh → nếu khác → POST `/api/ingest/tft-static`.
- **D-05:** **Backend giữ state** — endpoint `GET /api/patch/current` trả về patch version đã ingest gần nhất (từ `latest_version.txt` trong cache). State nằm trong DB/cache cùng với chunks, nhất quán và dễ debug bằng curl.
- **D-06:** Khi Riot CDN trả 403 (hoặc bất kỳ lỗi nào):
  - Backend ghi log chi tiết (patch, lỗi, timestamp)
  - n8n workflow bắn **Discord webhook notification** cho user biết: "Patch {version} detected — CDN blocked, manual intervention needed."
  - Không tự động thử CommunityDragon fallback (để tránh rủi ro sai data)
- **D-07:** Notification channel: **Discord webhook** (URL được cấu hình trong `.env` / n8n credential). Không dùng email.
- **D-08:** n8n workflow lưu Discord webhook URL trong **n8n Credential** (encrypted, không hardcode trong JSON).

### ngrok (D-09)
- **D-09:** **BỎ HOÀN TOÀN ngrok** khỏi Phase 6. Hệ thống chạy 100% local. Không cần expose webhook, không cần truy cập từ xa. Giữ đơn giản và an toàn.

### n8n ↔ Backend Auth (D-10 to D-11)
- **D-10:** Tất cả ingest endpoint (`POST /api/ingest/obsidian`, `POST /api/ingest/tft-static`) yêu cầu **Bearer token auth**. Header: `Authorization: Bearer <SECRET>`.
- **D-11:** API secret key được cấu hình trong `.env` file:
  - Backend: đọc từ `API_SECRET_KEY` env var, validate trong middleware
  - n8n: lưu trong **n8n Credential** (encrypted), sử dụng trong HTTP Request node
- **D-12:** Think về "Defense in Depth" — ngay cả khi Docker network internal, có auth giúp hệ thống sẵn sàng mở rộng (future-proof) nếu sau này cần mở port ra ngoài.

### Docker Compose (D-13)
- **D-13:** Thêm `GENERIC_TIMEZONE=Asia/Ho_Chi_Minh` và `N8N_PROXY_HOPS=1` vào n8n service trong `docker-compose.yml` (AUTO-04 requirement). Đảm bảo n8n workflow chạy đúng timezone.

### Notification Format (D-14)
- **D-14:** Discord notification message format:
  ```
  🚨 TFT Copilot — Patch Ingest Failed
  Patch: {version}
  Error: {error_message}
  Action: Manual intervention required
  Time: {timestamp}
  ```

### Claude's Discretion
- Exact Discord webhook URL format và cách tạo webhook trong Discord channel
- n8n credential type cho API key và Discord webhook (n8n hỗ trợ generic credential)
- Whether to use n8n's built-in "Error Trigger" node hay tự handle error trong workflow
- Exact notification message format (icon, emoji, embed fields)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project context
- `.planning/PROJECT.md` — Vision, stack, constraints, TFT policy compliance
- `.planning/REQUIREMENTS.md` — AUTO-01, AUTO-02, AUTO-03, AUTO-04
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, dependencies
- `.planning/STATE.md` — Accumulated context, locked decisions from Phase 1-5

### Prior phase context
- `.planning/phases/01-environment-setup/01-CONTEXT.md` — Ollama, Supabase, Docker decisions
- `.planning/phases/02-backend-core/02-CONTEXT.md` — SSE format, mode system
- `.planning/phases/03-frontend-chat/03-CONTEXT.md` — Frontend patterns
- `.planning/phases/04-rag-foundation/04-CONTEXT.md` — RAG pipeline, hybrid search
- `.planning/phases/05-tft-static-data/05-CONTEXT.md` — TFT ingest pipeline, cache, CDN endpoints

### Existing code (read before implementing)
- `apps/backend/app/routes/ingest.py` — Ingest endpoints cần thêm auth middleware
- `apps/backend/scripts/ingest_obsidian.py` — Obsidian ingest logic (reused)
- `apps/backend/scripts/ingest_tft_static.py` — TFT ingest + `get_cached_version()` / `save_cached_version()`
- `apps/backend/scripts/patch_refresh.py` — `TFT_PATCH_CACHE` path pattern
- `apps/backend/app/config.py` — Settings class, thêm `api_secret_key`
- `apps/backend/app/main.py` — FastAPI app, CORS middleware
- `infra/docker-compose.yml` — n8n service, thêm timezone env vars
- `n8n/workflows/patch_check.json` — Existing workflow (cần update logic)
- `n8n/workflows/obsidian_ingest.json` — Existing workflow (cần convert sang webhook trigger)

### Config/env
- `infra/.env.example` — Template for env vars

</canonical_refs>

<codebase_context>
## Existing Code Insights

### Reusable Assets
- `scripts/ingest_obsidian.py` — `ingest_vault()` async function (reuse as-is)
- `scripts/ingest_tft_static.py` — `ingest_tft_static()` async function (reuse as-is)
- `scripts/ingest_tft_static.py` — `get_cached_version()` + `save_cached_version()` — state management
- `app/config.py` — Settings singleton — thêm `api_secret_key` setting
- `infra/docker-compose.yml` — n8n service definition — thêm timezone env vars
- `n8n/workflows/patch_check.json` — existing JSON structure — update trigger logic
- `n8n/workflows/obsidian_ingest.json` — existing JSON structure — convert to webhook

### Established Patterns
- Auth via Bearer token header — implement as FastAPI dependency
- Settings via `pydantic_settings.BaseSettings` with `.env` file
- Async DB calls via `pool.acquire()` context manager
- n8n workflow JSON format với nodes + connections
- n8n Credentials cho sensitive data (encrypted)

### Integration Points
- n8n (Docker) → `http://backend:8000/api/ingest/obsidian` (Bearer auth)
- n8n (Docker) → `http://backend:8000/api/ingest/tft-static` (Bearer auth)
- n8n (Docker) → `http://backend:8000/api/patch/current` (GET, no auth)
- n8n → Discord webhook URL (notification on failure)
- Backend → `scripts/ingest_tft_static.py` → `get_cached_version()` (state read)
- Backend → `scripts/ingest_tft_static.py` → `save_cached_version()` (state write)

</codebase_context>

<specifics>
## Specific Ideas

- **Backend state endpoint:** `GET /api/patch/current` — đọc `~/.tft-copilot/cache/latest_version.txt`, trả về `{"version": "17.1", "cached_at": "2026-04-22T10:00:00Z"}`
- **Discord notification embed:**
  - Title: "🚨 TFT Patch Ingest Failed"
  - Fields: Patch version, Error type, Action required, Timestamp
  - Color: Red (#FF0000)
- **Auth middleware:** FastAPI `Depends` — check `Authorization: Bearer <token>` header, reject 401 nếu sai/missing
- **n8n credential name:** `tftBackendApi` cho API key, `discordWebhook` cho Discord webhook URL
- **Docker env vars to add:** `GENERIC_TIMEZONE=Asia/Ho_Chi_Minh`, `N8N_PROXY_HOPS=1` → n8n service trong docker-compose.yml
- **Existing bug in obsidian_ingest.json:** URL là `/ingest` thay vì `/ingest/obsidian` — fix trong implementation

</specifics>

<deferred>
## Deferred Ideas

### Ideas for Future Phases
- ngrok cho truy cập từ xa — chỉ thêm khi có nhu cầu thực tế
- Email notification thay thế Discord — Phase v2 nếu Discord không phù hợp
- Obsidian file watcher (tự động ingest khi file thay đổi) — Phase v2 (RAG-12)
- CommunityDragon automatic fallback khi Riot 403 — Phase v2 (không làm tự động, user trigger thủ công)

### Not in Scope
- Scheduled Obsidian ingest (manual trigger only — D-01)
- ngrok tunnel (bỏ hoàn toàn — D-09)
- Automatic CommunityDragon fallback (D-06 — notification only)

---

*Phase: 06-automation*
*Context gathered: 2026-04-22*
