---
phase: 05-tft-static-data
reviewed: 2026-04-22T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - apps/backend/app/config.py
  - apps/backend/scripts/ingest_tft_static.py
  - apps/backend/app/routes/ingest.py
  - apps/backend/app/services/retrieval.py
  - apps/backend/app/routes/search.py
  - apps/backend/app/routes/chat.py
  - apps/backend/app/services/ollama.py
  - apps/backend/app/models.py
  - apps/backend/app/main.py
  - supabase/migrations/0003_hybrid_search_tft_patch.sql
findings:
  critical: 1
  warning: 1
  info: 4
  total: 6
status: issues_found
---

# Phase 05: TFT Static Data - Code Review Report

**Reviewed:** 2026-04-22
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

The Phase 5 implementation for TFT Static Data introduces patch-aware hybrid search, CDN downloading, per-patch caching, and embedding generation. Most code is well-structured with proper async patterns and parameterized SQL queries. However, there is one critical bug that will cause a runtime crash, plus several code quality improvements to consider.

## Critical Issues

### CR-01: KeyError on `result['chunks']` in CLI script

**File:** `apps/backend/scripts/ingest_tft_static.py:408`
**Issue:** The `ingest_tft_static` function returns a dict with keys `patch`, `status`, `ingested`, `skipped`, `total` - there is no `chunks` key. Accessing `result['chunks']` will raise a `KeyError` when running the script directly.

**Fix:**
```python
# Change line 408 from:
print(f"Patch {result['patch']}: {result['status']}, {len(result['chunks'])} chunks")

# To:
print(f"Patch {result['patch']}: {result['status']}, ingested={result['ingested']}, skipped={result['skipped']}, total={result['total']}")
```

## Warnings

### WR-01: Duplicate Settings Fields

**File:** `apps/backend/app/config.py:28-29` and `42-43`
**Issue:** `app_host` and `app_port` are defined twice in the `Settings` class. Pydantic's `extra="ignore"` means the second definition silently overwrites the first. This is confusing and could mask configuration issues.

**Fix:**
```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:54322/postgres"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embedding_model: str = "qwen3-embedding:4b"
    ollama_embedding_dims: int = 1024

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # RAG
    rag_top_k: int = 6
    rag_chunk_size: int = 2000
    rag_chunk_overlap: int = 500

    # Obsidian
    obsidian_vault_path: str = ""

    # Ollama keep_alive
    ollama_keep_alive: str = "15m"

    # Chat
    chat_history_window: int = 10

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173"]

    # n8n
    webhook_url: str = "http://localhost:5678/"
    n8n_proxy_hops: int = 1
    generic_timezone: str = "Asia/Ho_Chi_Minh"
    tz: str = "Asia/Ho_Chi_Minh"

    # TFT Cache
    tft_cache_dir: str = str(Path.home() / ".tft-copilot" / "cache")
```

## Info

### IN-01: Redundant task.result() calls

**File:** `apps/backend/scripts/ingest_tft_static.py:104-107`
**Issue:** `task.result()` is called twice per iteration, computing the same value twice.

**Fix:**
```python
return {
    data_type: task.result()
    for data_type, task in tasks.items()
    if (result := task.result()) is not None
}
```

### IN-02: Silent exception swallowing in fetch_json_safe

**File:** `apps/backend/scripts/ingest_tft_static.py:53-61`
**Issue:** All exceptions are swallowed silently. While this is intentional for handling retired TFT sets, consider logging the error for debugging purposes.

**Fix:**
```python
import logging

logger = logging.getLogger(__name__)

async def fetch_json_safe(url: str) -> dict | None:
    """Fetch JSON data from a URL, returning None on error (e.g. 403 for retired TFT sets)."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None
```

### IN-03: Silent failure in message persistence

**File:** `apps/backend/app/routes/chat.py:145-146`
**Issue:** Message persistence failures are silently ignored with a bare `except Exception: pass`. Consider logging this for debugging.

**Fix:**
```python
except Exception as e:
    logger.warning(f"Failed to persist assistant message: {e}")
```

### IN-04: Duplicate timeout parameter

**File:** `apps/backend/app/services/ollama.py:45`
**Issue:** `timeout=120.0` is specified twice (once in `AsyncClient` context manager and once in `client.post`). This is redundant but harmless.

**Fix:**
```python
response = await client.post(
    f"{self.base_url}/api/embed",
    json=payload,
)
# Remove the duplicate timeout=120.0 parameter
```

---

_Reviewed: 2026-04-22_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
