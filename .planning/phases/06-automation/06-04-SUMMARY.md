---
phase: "06-automation"
plan: "06-04"
subsystem: automation
tags: [automation, n8n, patch-monitor, discord]
key-files:
  created:
    - n8n/workflows/patch_monitor.json
  modified:
    - n8n/workflows/credentials.json
metrics:
  workflows_created: 1
  credentials_documented: 2
---

## Summary

Created the n8n Patch Monitor Workflow — a 6-hour scheduled automation that detects new TFT patches via Riot's versions.json, compares against the backend's cached state, triggers ingest if changed, and sends a Discord notification on ingest failure.

### What was built

1. **patch_monitor.json** — n8n workflow with:
   - Cron trigger every 6 hours (`0 */6 * * *`)
   - Parallel GET requests: Riot `versions.json` → extract first element as `latestVersion`, backend `/api/patch/current` → extract `$.version` as `cachedVersion`
   - IF node compares `latestVersion !== cachedVersion`
     - **True branch:** POST `/api/ingest/tft-static` with Bearer auth via `tftBackendApi` credential
     - **False branch:** Log "No new patch detected"
   - Error handler: On ingest failure → HTTP POST Discord webhook with red embed (color 15158332)

2. **credentials.json** — Updated to document both `tftBackendApi` and `discordWebhook` credentials

### Key design notes

- Auth: Uses `tftBackendApi` credential (same as obsidian workflow) — no hardcoded token
- Discord: Uses `discordWebhook` credential (created manually in n8n UI)
- Error routing: `Version Mismatch?` IF node uses `onError: "continueErrorOutput"` to capture errors; `Trigger TFT Ingest` has its own `onError` pointing to Discord notification node
- Timing-safe token comparison used in backend auth middleware (`secrets.compare_digest()`)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | f250d4f | Create patch_monitor.json with 6-hour cron, state comparison, Discord notification |
| Task 2 | abaf2a0 | Add discordWebhook to credentials.json documentation |

## Deviations

**From plan JSON:** The plan's `Trigger TFT Ingest` node included the same `sendHeaders`/`headerParameters` bug fixed in wave 1. Implemented without that override — uses `tftBackendApi` credential directly (same pattern as fixed obsidian workflow).

## Manual Action Required

### 1. Create `discordWebhook` credential in n8n UI

1. Open Discord → right-click channel → Edit Channel → Integrations → Webhooks → New Webhook → Name: "TFT Copilot Alerts" → Copy Webhook URL
2. Open http://localhost:5678 → Settings → Credentials → Add Credential
3. Select **Custom Credentials** → **Generic Credential**
4. Fill in:
   - **Name:** `discordWebhook`
   - **URL:** Paste your Discord webhook URL (`https://discord.com/api/webhooks/...`)
5. Save

### 2. Create `tftBackendApi` credential in n8n UI (if not done from Wave 1)

1. Open http://localhost:5678 → Settings → Credentials → Add Credential
2. Select **Header Auth**
3. Fill in:
   - **Name:** `tftBackendApi`
   - **Header Name:** `Authorization`
   - **Header Prefix:** `Bearer ` (with trailing space)
   - **Header Value:** Your `API_SECRET_KEY` value from `.env`
4. Save

### 3. Set `API_SECRET_KEY` in `.env`

```bash
# Generate a key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to infra/.env:
API_SECRET_KEY=<generated-key>
```

### 4. Activate workflows in n8n UI

1. Open http://localhost:5678
2. Open **Obsidian Ingest Workflow** → toggle **Active** → Save
3. Open **Patch Monitor Workflow** → toggle **Active** → Save

## Verification

All checks passed:

```
grep "0 */6 * * *" n8n/workflows/patch_monitor.json  → found
grep "versions.json" n8n/workflows/patch_monitor.json  → found
grep "api/patch/current" n8n/workflows/patch_monitor.json  → found
grep "api/ingest/tft-static" n8n/workflows/patch_monitor.json  → found
grep "15158332" n8n/workflows/patch_monitor.json  → found
grep "tftBackendApi" n8n/workflows/patch_monitor.json  → found
grep "discordWebhook" n8n/workflows/patch_monitor.json  → found
grep "discordWebhook" n8n/workflows/credentials.json  → found
```

## Self-Check: PASSED

- [x] `n8n/workflows/patch_monitor.json` created with 6-hour cron trigger
- [x] Workflow calls GET `/api/patch/current` and compares with Riot `versions.json`
- [x] Workflow calls POST `/api/ingest/tft-static` with Bearer auth via `tftBackendApi` credential
- [x] On ingest failure, HTTP error routes to Discord notification with red embed (color 15158332)
- [x] `credentials.json` documents both `tftBackendApi` and `discordWebhook`
- [x] Manual steps documented for creating both credentials in n8n UI
