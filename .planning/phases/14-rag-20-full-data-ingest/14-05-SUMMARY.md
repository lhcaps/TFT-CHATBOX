---
phase: 14
plan: 05
subsystem: backend
tags: [watchdog, reactive-sync, obsidian, file-watcher]

requires:
  - phase: 14-01
    provides: entity_type column + document_chunks table
provides:
  - FileSystemWatcher with watchdog integration
  - POST /api/watch/start, /api/watch/stop, /api/watch/status, /api/watch/events
affects: []

tech-stack:
  added: [watchdog]
  patterns: [singleton watcher, debounce, hash-based change detection]

key-files:
  created:
    - apps/backend/app/services/watcher.py
    - apps/backend/app/routes/watch.py
  modified:
    - apps/backend/app/main.py
    - apps/backend/requirements.txt

key-decisions:
  - "watchdog try/except import — graceful fallback if not installed"
  - "500ms debounce via threading.Timer before triggering ingest"

patterns-established:
  - "FileSystemWatcher singleton pattern for process-wide background task"

requirements-completed: [RAG2-05]

duration: 12min
completed: 2026-04-23

---

# Phase 14: Plan 05 — Obsidian File Watcher Summary

**FileSystemWatcher with watchdog integration triggers reactive re-embed on .md file changes — 500ms debounce, hash-based dedup**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-23T00:55:00Z
- **Completed:** 2026-04-23T01:07:00Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- watchdog>=4.0.0 added to requirements.txt
- FileSystemWatcher singleton with watchdog Observer integration
- ObsidianFileHandler: 500ms debounce before triggering reactive ingest
- Hash-based change detection: skip re-ingest if content hash unchanged
- _reingest_file: chunk + embed + upsert single .md file to document_chunks
- POST /api/watch/start: start watching vault (or use OBSIDIAN_VAULT_PATH env var)
- POST /api/watch/stop: stop watching
- GET /api/watch/status: current watching state
- GET /api/watch/events: recent file change events
- Watch router registered in main.py

## Files Created/Modified

- `apps/backend/app/services/watcher.py` — FileSystemWatcher + ObsidianFileHandler
- `apps/backend/app/routes/watch.py` — watch router with /start, /stop, /status, /events
- `apps/backend/app/main.py` — watch router registered
- `apps/backend/requirements.txt` — watchdog>=4.0.0 added

## Decisions Made

- watchdog try/except import — graceful ImportError if not installed
- 500ms debounce via threading.Timer (non-blocking)
- Singleton FileSystemWatcher — one watcher per process

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- File watcher ready for deployment
- Run `pip install watchdog` to install dependency

---
*Phase: 14-rag-20-full-data-ingest*
*Completed: 2026-04-23*
