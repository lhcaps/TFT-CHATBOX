# Phase 8: Patch Meta Mastery — Plans

**Phase:** 8
**Goal:** Automated TFT patch intelligence — backend persists patch state in DB, n8n monitors Riot, auto-ingests patch notes + static data, frontend shows patch version + staleness.
**Requirements:** PATCH-01, PATCH-02, PATCH-03, PATCH-04, PATCH-05

---

## Plan 08-01: Database Schema — `patch_info` Table

**wave:** 1
**files_modified:** `supabase/migrations/0004_patch_info_table.sql`
**requirements:** PATCH-01
**type:** execute

### `<objective>`
Create `patch_info` DB table as single source of truth for patch state. Refactor `GET /api/patch/current` to read from DB.

### `<tasks>`

**Task 1: Create migration for `patch_info` table**

`<read_first>`
- `supabase/migrations/0001_initial_schema.sql`
- `apps/backend/app/routes/patch_state.py`
</read_first>`

`<action>`
Create file `supabase/migrations/0004_patch_info_table.sql`:

```sql
-- Patch state table as single source of truth
CREATE TABLE IF NOT EXISTS patch_info (
    id SERIAL PRIMARY KEY,
    current_patch VARCHAR(16) NOT NULL DEFAULT '',
    latest_available VARCHAR(16) NOT NULL DEFAULT '',
    last_checked TIMESTAMPTZ,
    last_ingested TIMESTAMPTZ,
    ingest_status VARCHAR(32) DEFAULT 'idle',  -- idle | running | success | failed
    ingest_error TEXT,
    patch_notes_url TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed with current state (patch 17.1)
INSERT INTO patch_info (id, current_patch, latest_available, last_checked, last_ingested, ingest_status)
VALUES (1, '17.1', '17.1', NOW(), NOW(), 'success')
ON CONFLICT (id) DO NOTHING;

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS patch_info_updated_idx ON patch_info (updated_at DESC);
```
</action>`

`<acceptance_criteria>`
- `supabase/migrations/0004_patch_info_table.sql` created with CREATE TABLE IF NOT EXISTS patch_info
- Table has columns: id, current_patch, latest_available, last_checked, last_ingested, ingest_status, ingest_error, patch_notes_url, updated_at
- Seed row inserted for patch 17.1
- Migration tested: apply via `npx supabase db push` and verify table exists
</acceptance_criteria>`

**Task 2: Refactor `GET /api/patch/current` to read from DB**

`<read_first>`
- `apps/backend/app/routes/patch_state.py`
- `apps/backend/app/db.py`
</read_first>`

`<action>`
Replace the file content of `apps/backend/app/routes/patch_state.py`:

```python
"""Patch state endpoint — reads from DB patch_info table."""
from __future__ import annotations

import logging
from fastapi import APIRouter

from app.db import get_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patch", tags=["patch"])


@router.get("/current")
async def get_current_patch() -> dict:
    """Return the currently cached TFT patch version from DB.

    Returns:
        {"version": "17.1"} when a version has been set.
        {"version": None} when no version is set.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT current_patch FROM patch_info WHERE id = 1")
    if row is None or not row["current_patch"]:
        return {"version": None}
    return {"version": row["current_patch"]}
```

Also update the imports in `app/routes/__init__.py` if needed (verify the router is included in main.py — it already is as `patch_state`).
</action>`

`<acceptance_criteria>`
- `GET /api/patch/current` returns `{"version": "17.1"}` from DB after migration
- Returns `{"version": null}` if no row in patch_info
- Endpoint tested with curl: `curl http://localhost:8000/api/patch/current`
</acceptance_criteria>`

### `<verification>`
1. Apply migration: `npx supabase db push` in `infra/` directory
2. Test `GET /api/patch/current` returns correct version
3. Verify table has `patch_info` row with `current_patch = '17.1'`

### `<success_criteria>`
- [ ] `patch_info` table exists with all required columns
- [ ] `GET /api/patch/current` returns version from DB
- [ ] Migration file committed to git

---

## Plan 08-02: Backend API — Patch Status + Patch Notes Ingest

**wave:** 2
**files_modified:** `apps/backend/app/routes/patch_state.py`, `apps/backend/scripts/scrape_patch17.py`, `apps/backend/app/routes/ingest.py`
**requirements:** PATCH-02, PATCH-03
**type:** execute

### `<objective>`
Add `GET /api/patch/status` (full DB state) and `POST /api/ingest/patch-notes` (scrape + ingest). Refactor `scrape_patch17.py` into reusable functions.

### `<tasks>`

**Task 1: Add `GET /api/patch/status` endpoint**

`<read_first>`
- `apps/backend/app/routes/patch_state.py`
- `.planning/phases/08-patch-meta-mastery/08-CONTEXT.md`
</read_first>`

`<action>`
Append to `apps/backend/app/routes/patch_state.py`:

```python
@router.get("/status")
async def get_patch_status() -> dict:
    """Return full patch state from DB.

    Returns:
        {
            "current": "17.1",
            "latest_available": "17.1",
            "last_checked": "2026-04-22T...",
            "last_ingested": "2026-04-22T...",
            "is_stale": False,
            "ingest_status": "idle",
            "patch_notes_url": null
        }
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT current_patch, latest_available, last_checked, last_ingested, ingest_status, patch_notes_url FROM patch_info WHERE id = 1"
        )
    if row is None:
        return {"error": "patch_info not initialized"}
    is_stale = bool(row["latest_available"]) and row["latest_available"] != row["current_patch"]
    return {
        "current": row["current_patch"] or None,
        "latest_available": row["latest_available"] or None,
        "last_checked": row["last_checked"].isoformat() if row["last_checked"] else None,
        "last_ingested": row["last_ingested"].isoformat() if row["last_ingested"] else None,
        "is_stale": is_stale,
        "ingest_status": row["ingest_status"],
        "patch_notes_url": row["patch_notes_url"],
    }
```

Also add the `Depends(verify_api_key)` version for n8n to update status:

```python
@router.post("/status/refresh")
async def refresh_patch_status(
    patch: str | None = None,
    _: str = Depends(verify_api_key),
) -> dict:
    """Refresh latest_available from Riot CDN. Called by n8n workflow."""
    from scripts.ingest_tft_static import get_latest_version

    pool = await get_pool()
    latest = patch
    if latest is None:
        try:
            latest = await get_latest_version()
        except Exception as e:
            return {"error": f"Failed to fetch latest: {e}"}

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE patch_info SET latest_available = $1, last_checked = NOW(), updated_at = NOW() WHERE id = 1",
            latest,
        )
    return {"latest_available": latest}
```
</action>`

`<acceptance_criteria>`
- `GET /api/patch/status` returns full state: current, latest_available, last_checked, last_ingested, is_stale, ingest_status, patch_notes_url
- `POST /api/patch/status/refresh` (requires auth) updates latest_available in DB
- Both tested via curl
</acceptance_criteria>`

**Task 2: Refactor `scrape_patch17.py` into reusable module**

`<read_first>`
- `apps/backend/scripts/scrape_patch17.py`
- `apps/backend/scripts/ingest_tft_static.py` §get_latest_version
</read_first>`

`<action>`
Refactor `apps/backend/scripts/scrape_patch17.py` to expose reusable functions. The existing `scrape_patch_notes()`, `format_as_markdown()`, and `ingest_into_db()` functions are already reusable — just add a `PATCH_URL_TEMPLATE` and make the patch version configurable:

1. Add at top of file:
```python
# Template URL for patch notes — version injected at runtime
PATCH_NOTES_LISTING_URL = "https://teamfighttactics.leagueoflegends.com/en-us/news/"
PATCH_NOTES_URL_TEMPLATE = "https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-{major}-{minor}/"
```

2. Add `scrape_patch_url()` function that finds the patch URL from the listing page:
```python
def scrape_patch_url(patch_version: str) -> str | None:
    """Find the patch notes URL for a given patch version by scraping the listing page.

    Searches for URL pattern: /teamfight-tactics-patch-{major}-{minor}/
    Returns the full URL or None if not found.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    # Parse major.minor from "17.1" -> "17", "1"
    parts = patch_version.split(".")
    major, minor = parts[0], parts[1] if len(parts) > 1 else "0"
    target_pattern = f"teamfight-tactics-patch-{major}-{minor}"

    try:
        r = httpx.get(PATCH_NOTES_LISTING_URL, timeout=30.0, headers=headers)
        r.raise_for_status()
    except Exception:
        # Fallback to constructed URL
        return PATCH_NOTES_URL_TEMPLATE.format(major=major, minor=minor)

    # Find all patch links
    import re
    pattern = re.compile(r'href="([^"]*teamfight-tactics-patch[^"]+)"')
    matches = pattern.findall(r.text)
    for href in matches:
        if target_pattern in href:
            if href.startswith("/"):
                return f"https://teamfighttactics.leagueoflegends.com{href}"
            return href

    # Fallback
    return PATCH_NOTES_URL_TEMPLATE.format(major=major, minor=minor)
```

3. Rename `main()` to `scrape_and_ingest(patch: str | None = None)`:
```python
async def scrape_and_ingest(patch: str | None = None) -> dict:
    """Scrape patch notes and ingest into DB. If patch is None, auto-detect latest."""
    if patch is None:
        from scripts.ingest_tft_static import get_latest_version
        patch = await get_latest_version()

    patch_url = scrape_patch_url(patch)
    ...
```
</action>`

`<acceptance_criteria>`
- `scrape_patch_url("17.1")` returns the correct Riot patch URL
- `scrape_patch_url("17.2")` returns a valid URL (or falls back to template)
- Existing `main()` still works as CLI entry point (backward compat)
- `asyncio.run(scrape_and_ingest("17.1"))` can be called programmatically
</acceptance_criteria>`

**Task 3: Add `POST /api/ingest/patch-notes` endpoint**

`<read_first>`
- `apps/backend/app/routes/ingest.py`
- `apps/backend/scripts/scrape_patch17.py`
</read_first>`

`<action>`
Add to `apps/backend/app/routes/ingest.py`:

```python
@router.post("/patch-notes")
async def ingest_patch_notes_route(
    patch: str | None = None,
    _: str = Depends(verify_api_key),
) -> dict:
    """Scrape TFT patch notes from Riot and ingest into DB.

    Args:
        patch: Optional patch version (e.g. "17.1"). If omitted, uses latest from DB or CDN.

    Scrape flow:
    1. Get patch version (param or latest_available from patch_info or CDN)
    2. Find patch URL via listing page scrape or URL pattern
    3. Scrape content with BeautifulSoup
    4. Chunk, embed, and ingest into chunks table
    5. Update patch_info: current_patch + last_ingested
    """
    from scripts.scrape_patch17 import scrape_and_ingest
    from app.db import get_pool

    # Resolve patch version
    resolved_patch = patch
    if resolved_patch is None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT latest_available FROM patch_info WHERE id = 1")
            if row and row["latest_available"]:
                resolved_patch = row["latest_available"]

    if resolved_patch is None:
        raise HTTPException(status_code=400, detail="No patch version available. Pass ?patch=X.Y or set latest_available in DB.")

    # Update status to running
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE patch_info SET ingest_status = 'running', ingest_error = NULL, updated_at = NOW() WHERE id = 1"
        )

    try:
        stats = await scrape_and_ingest(resolved_patch)

        # Update patch_info on success
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE patch_info
                SET current_patch = $1,
                    latest_available = $1,
                    last_ingested = NOW(),
                    ingest_status = 'success',
                    ingest_error = NULL,
                    updated_at = NOW()
                WHERE id = 1
                """,
                resolved_patch,
            )
        return {"status": "ok", "patch": resolved_patch, **stats}
    except Exception as e:
        logger.exception("Patch notes ingest failed")
        # Update status to failed
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE patch_info SET ingest_status = 'failed', ingest_error = $1, updated_at = NOW() WHERE id = 1",
                str(e)[:500],
            )
        raise HTTPException(status_code=500, detail=f"Patch notes ingest failed: {e}")
```
</action>`

`<acceptance_criteria>`
- `POST /api/ingest/patch-notes` (authed) triggers scrape + ingest pipeline
- `POST /api/ingest/patch-notes?patch=17.1` ingests patch 17.1
- On success: `patch_info` updated with `current_patch`, `last_ingested`, `ingest_status='success'`
- On failure: `ingest_status='failed'`, `ingest_error` set
- Existing `POST /api/ingest/obsidian` still works unchanged
</acceptance_criteria>`

### `<verification>`
1. `curl -X POST http://localhost:8000/api/ingest/patch-notes -H "Authorization: Bearer $API_SECRET_KEY"` — triggers full pipeline
2. `curl http://localhost:8000/api/patch/status` — shows updated state
3. `SELECT * FROM patch_info` — shows current_patch, ingest_status

### `<success_criteria>`
- [ ] `GET /api/patch/status` returns full patch state from DB
- [ ] `POST /api/patch/status/refresh` updates latest_available
- [ ] `scrape_patch_url()` finds patch URL from listing page
- [ ] `POST /api/ingest/patch-notes` scrapes and ingests patch notes
- [ ] `patch_info` updated after successful ingest

---

## Plan 08-03: n8n Workflow — Activate + Patch Notes + Discord

**wave:** 2
**files_modified:** `n8n/workflows/patch_monitor.json`
**requirements:** PATCH-04
**type:** execute

### `<objective>`
Activate `patch_monitor.json`, extend to also trigger patch-notes ingest, and add verbose Discord notifications (start + success/fail).

### `<tasks>`

**Task 1: Update `patch_monitor.json` workflow**

`<read_first>`
- `n8n/workflows/patch_monitor.json`
- `n8n/workflows/credentials.json`
</read_first>`

`<action>`
Create updated `n8n/workflows/patch_monitor.json` with the following changes:
1. Keep existing `Scheduled Trigger` (every 6h: `0 */6 * * *`)
2. Keep `Get Riot Version` (GET https://ddragon.leagueoflegends.com/api/versions.json)
3. Keep `Get Backend Cached Version` (GET http://backend:8000/api/patch/current)
4. Replace `Version Mismatch?` condition to check: `latest != current` (use `$json[0]` vs `$('Get Backend Cached Version').item.json.version`)
5. On TRUE branch (new version detected):
   a. `Discord Start`: POST to Discord webhook with "TFT Patch {version} detected! Starting ingest..."
   b. `Trigger Static Ingest`: POST http://backend:8000/api/ingest/tft-static (with API key header)
   c. `Trigger Patch Notes`: POST http://backend:8000/api/ingest/patch-notes?patch={version} (with API key header)
   d. `Discord Success`: POST to Discord with "Ingest complete: {n} new chunks / {m} skipped"
6. On FALSE branch (no new version): `Log: No Change` (existing)
7. On ERROR (any node fails): `Discord Fail`: POST with "TFT ingest FAILED: {error.message}"

Node ordering: Trigger → Get Riot → Get Backend → Version Mismatch → [TRUE: Discord Start → Static Ingest → Patch Notes → Discord Success] / [FALSE: Log] / [ERROR: Discord Fail]

Credentials: `tftBackendApi` (httpHeaderAuth) and `discordWebhook` already exist from v1.0.

Important: Set `"active": true` in the workflow JSON.
</action>`

`<acceptance_criteria>`
- `"active": true` in updated patch_monitor.json
- Workflow triggers both `/api/ingest/tft-static` AND `/api/ingest/patch-notes` when new patch detected
- Discord sends: (1) start message, (2) success message with chunk counts, (3) fail message with error
- All nodes have correct credentials referenced
- Workflow file is valid JSON (verify with `python -c "import json; json.load(open('n8n/workflows/patch_monitor.json'))"`)
</acceptance_criteria>`

**Task 2: Verify credentials exist**

`<read_first>`
- `n8n/workflows/credentials.json`
</read_first>`

`<action>`
Check `n8n/workflows/credentials.json` for:
- `tftBackendApi` — HTTP Header Auth with API_SECRET_KEY
- `discordWebhook` — Discord webhook URL

If `discordWebhook` is missing or placeholder, note that user needs to configure it in n8n UI. Add a comment in the workflow about this requirement.

If `tftBackendApi` is missing, create an entry:
```json
"tftBackendApi": {
  "name": "TFT Backend API",
  "type": "httpHeaderAuth",
  "data": {
    "headerName": "Authorization",
    "headerValue": "Bearer <API_SECRET_KEY>"
  }
}
```
(Note: in practice, n8n credential values should be set in n8n UI, not hardcoded — add a TODO comment.)
</action>`

`<acceptance_criteria>`
- credentials.json has entries for both tftBackendApi and discordWebhook (or clear TODO)
- User can import the workflow in n8n and configure the API key and Discord webhook in n8n UI
</acceptance_criteria>`

### `<verification>`
1. Open n8n at http://localhost:5678
2. Import `patch_monitor.json`
3. Activate the workflow (toggle switch)
4. Verify: Trigger → check logs for correct node execution order

### `<success_criteria>`
- [ ] n8n workflow updated with all new nodes
- [ ] `"active": true` set in workflow
- [ ] Both ingest endpoints called on new patch
- [ ] Discord notifications for start/success/fail

---

## Plan 08-04: Frontend — Patch Version Badge + Check Button

**wave:** 3
**files_modified:** `apps/frontend/src/App.tsx`, `apps/frontend/src/components/PatchStatus.tsx` (new)
**requirements:** PATCH-05
**type:** execute
**depends_on:** 08-02

### `<objective>`
Add patch version badge and "Check for updates" button to frontend. Display staleness state (up to date / stale).

### `<tasks>`

**Task 1: Create `PatchStatus` component**

`<read_first>`
- `apps/frontend/src/App.tsx`
- `apps/frontend/tailwind.config.js` or CSS variables for colors
</read_first>`

`<action>`
Create `apps/frontend/src/components/PatchStatus.tsx`:

```tsx
import { useState, useEffect } from "react";

interface PatchStatus {
  current: string | null;
  latest_available: string | null;
  is_stale: boolean;
  ingest_status: string;
  last_ingested: string | null;
}

export function PatchStatus() {
  const [status, setStatus] = useState<PatchStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/patch/status");
      if (res.ok) {
        setStatus(await res.json());
      }
    } catch {
      // silently ignore — patch status is non-critical
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh every 30 minutes
    const interval = setInterval(fetchStatus, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleCheck = async () => {
    setChecking(true);
    await fetchStatus();
    setChecking(false);
  };

  if (loading && !status) {
    return (
      <span className="text-xs text-zinc-500">Checking patch...</span>
    );
  }

  if (!status?.current) {
    return null;
  }

  const isStale = status.is_stale;

  return (
    <div className="flex items-center gap-2">
      <span
        className={`text-xs font-mono px-2 py-0.5 rounded border ${
          isStale
            ? "border-yellow-600 text-yellow-400 bg-yellow-950"
            : "border-green-700 text-green-400 bg-green-950"
        }`}
      >
        Patch {status.current}
      </span>
      {isStale && (
        <span className="text-xs text-yellow-400">
          {status.latest_available} available
        </span>
      )}
      {!isStale && (
        <span className="text-xs text-green-600">up to date</span>
      )}
      <button
        onClick={handleCheck}
        disabled={checking}
        className="text-xs text-zinc-400 hover:text-zinc-200 disabled:opacity-50 transition-colors"
        title="Check for updates"
      >
        {checking ? "..." : "↻"}
      </button>
    </div>
  );
}
```
</action>`

`<acceptance_criteria>`
- `PatchStatus` component renders: "Patch 17.1" badge
- Badge is green when up to date, yellow when stale
- "↻" button triggers refresh
- Component fetches from `GET /api/patch/status`
- Returns null if no patch is set (graceful degradation)
</acceptance_criteria>`

**Task 2: Add `PatchStatus` to App header**

`<read_first>`
- `apps/frontend/src/App.tsx`
</read_first>`

`<action>`
Add import to `App.tsx`:
```tsx
import { PatchStatus } from "./components/PatchStatus";
```

Add `<PatchStatus />` in the header area of App.tsx. Look for the existing header/nav area (around line 12-20) and add:
```tsx
<header className="flex items-center justify-between p-3 border-b border-zinc-700">
  <h1 className="font-bold text-sm text-zinc-200">TFT Copilot</h1>
  <PatchStatus />
</header>
```

Place the `<PatchStatus />` component in the existing header or add one if none exists. Preserve all existing functionality.
</action>`

`<acceptance_criteria>`
- App renders with patch version badge visible
- Badge updates when status changes
- All existing chat functionality unchanged
</acceptance_criteria>`

### `<verification>`
1. Start frontend: `cd apps/frontend && npm run dev`
2. Verify patch badge appears in header
3. Verify stale state shows correctly (test with different patch versions)
4. Click "↻" button and verify status refreshes

### `<success_criteria>`
- [ ] Patch badge visible in frontend header
- [ ] Green badge when up to date, yellow when stale
- [ ] "Check for updates" button works
- [ ] All existing app functionality preserved

---

## Phase 8 Verification

### Overall Success Criteria

1. `npx supabase db push` applies 0004_patch_info_table.sql successfully
2. `GET /api/patch/status` returns full patch state from DB
3. `POST /api/ingest/patch-notes` scrapes Riot page and ingests into chunks
4. `n8n/workflows/patch_monitor.json` is `active: true` with all nodes connected
5. Frontend shows patch version badge with staleness state
6. End-to-end: new patch detected → both ingest endpoints triggered → Discord notified

### Manual Verification Steps

```powershell
# 1. Apply migration
cd infra; npx supabase db push

# 2. Check DB state
curl http://localhost:8000/api/patch/status

# 3. Trigger patch notes ingest (with auth)
$headers = @{ Authorization = "Bearer $env:API_SECRET_KEY" }
Invoke-RestMethod -Uri "http://localhost:8000/api/ingest/patch-notes?patch=17.1" -Method POST -Headers $headers

# 4. Check updated state
curl http://localhost:8000/api/patch/status

# 5. Check chunks in DB
# Query: SELECT source, count(*) FROM chunks WHERE source LIKE 'tft_patch_notes%' GROUP BY source

# 6. Open n8n at http://localhost:5678, import patch_monitor.json, activate
```

### Must-Haves (Goal-Backward)

1. Backend reads patch state from DB — file no longer used as source of truth
2. `POST /api/ingest/patch-notes` can be called by n8n with auth to trigger full scrape+ingest pipeline
3. n8n workflow is `active: true` and calls both static and notes ingest on new patch detection
4. Frontend shows current patch version with up-to-date/stale state
5. Discord sends start + completion notification on new patch ingest
