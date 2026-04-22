# Phase 8: Patch Meta Mastery - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 08-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 08-patch-meta-mastery
**Areas discussed:** Patch state storage, Patch notes API, Discord notifications, Frontend patch display, Patch URL discovery

---

## Patch State Storage

| Option | Description | Selected |
|--------|-------------|----------|
| DB table (recommended) | queryable, testable, single source of truth | ✅ |
| Keep file-based | simpler, existing code mostly works | |

**User's choice:** DB table (recommended) — queryable, testable, single source of truth

**Notes:** User wants structured, queryable patch state in DB rather than file-based approach.

---

## Patch Notes API

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated endpoint POST /api/ingest/patch-notes | n8n calls this after static ingest | ✅ |
| Extend POST /api/ingest/tft-static | add optional patch_notes flag | |
| Script only | Keep as standalone script, n8n calls Python directly | |

**User's choice:** Dedicated endpoint POST /api/ingest/patch-notes

**Notes:** Clean separation of concerns — static data vs patch notes scraping are different operations.

---

## Discord Notification

| Option | Description | Selected |
|--------|-------------|----------|
| New patch detected only | "TFT 17.2 is out! Ingest started." | |
| New patch + ingest success/fail | more verbose | ✅ |
| Skip Discord for now | logs in n8n console only | |

**User's choice:** New patch + ingest success/fail

**Notes:** Wants visibility into both start and completion/failure of ingest process.

---

## Frontend Patch Display

| Option | Description | Selected |
|--------|-------------|----------|
| Version badge + "Stale" label | minimal, clear | |
| Version badge + "Check for updates" button | let user trigger check manually | ✅ |
| Version badge + auto-refresh every 6h | always fresh, no user action | |

**User's choice:** Version badge + "Check for updates" button

**Notes:** Manual check gives user control; auto-refresh might be too aggressive for a local app.

---

## Patch URL Discovery

| Option | Description | Selected |
|--------|-------------|----------|
| Scrape listing page | find patch URL dynamically | ✅ |
| URL pattern + version | riot.com/news/.../patch-{major}-{minor}/ | |
| Hardcode current set prefix | fetch all, filter by pattern | |

**User's choice:** Scrape listing page — find patch URL dynamically

**Notes:** Most reliable approach that works across set transitions without hardcoding.

---

## Deferred Ideas

- Auto-ingest on button click — add to backlog
- Multiple patch version history support — future phase
- Browser notifications — future phase

---
