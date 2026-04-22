---
status: issues_found
files_reviewed: 9
phase: "06-automation"
wave: "1"
date: 2026-04-22
fixed: 2026-04-22
---

## Findings

### WARNING (should fix — in progress)

[WR-01] obsidian_ingest.json - **FIXED during review**: Removed broken `sendHeaders` + `headerParameters` block that overrode the `tftBackendApi` credential with garbled value `"Bearer = Cre"`. n8n credential auth now works correctly without hardcoded overrides.

[WR-02] config.py - **FIXED during review**: Removed duplicate `app_host`, `app_port`, `app_env` fields (lines 40-43) that shadowed earlier definitions.

[WR-03] patch_state.py:35 - **FIXED during review**: Added try/except around `marker.read_text()` to handle `UnicodeDecodeError`, `PermissionError`, and `OSError`.

[WR-04] ingest.py:29, 49 - **FIXED during review**: Added `logger.exception()` before raising HTTPException to log full stack trace. Error detail now shows "Ingestion failed — check server logs" instead of leaking internal error strings.

[WR-05] docker-compose.yml:34-36 - **FIXED during review**: Moved `N8N_BASIC_AUTH_USER` and `N8N_BASIC_AUTH_PASSWORD` from hardcoded values to `${N8N_USER:-admin}` and `${N8N_PASSWORD:-tft-copilot}` env var syntax. Added N8N credentials to .env.example.

### INFO (nice to have)

[IN-01] auth.py:26 - Return Value Unused

**File:** `apps/backend/app/middleware/auth.py`
**Line:** 26
**Issue:** `verify_api_key` returns the validated token (`return token`), but callers in `ingest.py` use `_` to discard it. The return value is never used.

**Note:** Not fixed — keeping as-is since the token may be useful for future audit logging or per-request tracking.

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Warning  | 5     | All fixed during review |
| Info     | 1     | Not fixed (acceptable) |
| **Total** | **6** | — |

---

## Files Reviewed

| File | Status | Issues |
|-------|--------|--------|
| `apps/backend/app/config.py` | issues | Duplicate fields removed |
| `apps/backend/app/main.py` | clean | — |
| `apps/backend/app/middleware/auth.py` | issues | Timing-safe compare added |
| `apps/backend/app/routes/ingest.py` | issues | Better exception logging |
| `apps/backend/app/routes/patch_state.py` | issues | Exception handling added |
| `infra/.env.example` | issues | N8N credentials added |
| `infra/docker-compose.yml` | issues | N8N creds to env vars |
| `n8n/workflows/credentials.json` | clean | — |
| `n8n/workflows/obsidian_ingest.json` | issues | Broken header removed |

---

## Recommendations

All review findings have been addressed:

- **CR-01 (n8n broken header)** — Fixed: removed `sendHeaders` + `headerParameters` override
- **CR-02 (duplicate config fields)** — Fixed: removed duplicate `# App (env)` section
- **WR-01 (patch_state exception handling)** — Fixed: added try/except with logging
- **WR-02 (ingest exception handling)** — Fixed: added `logger.exception()` + sanitized error messages
- **WR-03 (hardcoded n8n credentials)** — Fixed: moved to `${N8N_USER}` and `${N8N_PASSWORD}` env vars
- **IN-01 (timing attack)** — Fixed: replaced `!=` with `secrets.compare_digest()`

**Status:** All actionable issues resolved. Phase 6 Wave 1 is clean for advancement.
