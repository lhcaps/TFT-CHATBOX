---
phase: 06-automation
plan: "06-03"
subsystem: automation
tags: [automation, n8n, obsidian]
key-files:
  created:
    - n8n/workflows/credentials.json
  modified:
    - n8n/workflows/obsidian_ingest.json
metrics:
  workflows_updated: 1
  manual_steps: 1
---

## Summary

Updated the n8n Obsidian ingest workflow to use a manual webhook trigger instead of a cron schedule. The workflow now triggers via HTTP POST to a manual webhook endpoint and authenticates with the backend using Bearer token authentication through the `tftBackendApi` credential stored securely in n8n.

## Commits

| Task | Commit |
|------|--------|
| Task 1 | 80b851c |
| Task 2 | 7429bd4 |

## Deviations

None - plan executed exactly as written.

## Manual Action Required

**Creating tftBackendApi Credential in n8n UI:**

1. Open n8n UI at http://localhost:5678 and log in with `admin` / `tft-copilot`
2. Click the gear icon (Settings) in the top-right
3. Go to **Credentials**
4. Click **Add Credential**
5. Select **Header Auth**
6. Fill in:
   - **Name:** `tftBackendApi`
   - **Header Name:** `Authorization`
   - **Header Prefix:** `Bearer ` (including the space)
   - **Header Value:** Your `API_SECRET_KEY` value from `.env`
7. Click **Save**

## Verification

All checks passed:
- `webhook` found in workflow (manual trigger node)
- `http://backend:8000/api/ingest/obsidian` found (correct backend URL)
- `tftBackendApi` found (credential reference)
- `genericCredentialType` found (auth configuration)
- No `cron` or `interval` patterns found (schedule removed)

## Self-Check: PASSED

- obsidian_ingest.json updated with webhook trigger
- obsidian_ingest.json URL corrected to /api/ingest/obsidian
- obsidian_ingest.json uses tftBackendApi credential for auth
- No cron/schedule nodes remain in workflow
- credentials.json documents the required credential
- Manual step documented for creating credential in n8n UI
