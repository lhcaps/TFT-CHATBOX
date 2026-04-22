# 07-01 SUMMARY: TTL Embedding Cache

## What was built

Added a TTL-based LRU cache for query embeddings in `apps/backend/app/services/cache.py`. The cache stores both the embedding vector and the retrieved chunks, allowing cache hits to skip both Ollama AND the SQL hybrid search query.

## Files created/modified

| File | Change |
|------|--------|
| `apps/backend/app/services/cache.py` | **NEW** — `EmbeddingCache` class using `cachetools.TTLCache` |
| `apps/backend/app/config.py` | Added `embedding_cache_max_size` (500) and `embedding_cache_ttl_seconds` (1800) |
| `apps/backend/app/services/retrieval.py` | Integrated cache.get/set into `retrieve_chunks()` with mode parameter |
| `apps/backend/app/services/ollama.py` | Added `RetrievedChunk` dataclass for type-safe chunk storage |
| `apps/backend/requirements.txt` | Added `cachetools==5.5.0` |

## Key design decisions

- **Cache key format**: `"{mode}:{patch_or_all}:{query}"` — same query in different modes/patches misses cache
- **Cache stores full results**: Both embedding + chunks stored; cache hit returns chunks directly without calling Ollama or Postgres
- **TTL + LRU eviction**: `cachetools.TTLCache` handles both TTL (default 30 min) and LRU (default 500 entries)
- **Process-level singleton**: `embedding_cache = EmbeddingCache()` module-level instance

## Verification results

All acceptance criteria passed:

```
Cache set/get: OK
TTL eviction: OK
Import chain OK
TTL=1800s, max=500
```

### grep verification

| Check | Result |
|-------|--------|
| `grep -n "TTLCache" cache.py` | Lines 8, 35 |
| `grep -n "embedding_cache" retrieval.py` | Lines 7, 29, 77 (import, get, set) |
| `grep -n "from app.services.cache import" retrieval.py` | Line 7 |

## Performance target

- **Cache hit**: < 50ms (skips Ollama embedding + SQL hybrid_search)
- **Cache miss**: Normal latency (embedding generation + DB query)

## Notes

- `mode` parameter added to `retrieve_chunks()` for cache key isolation (normal/rag/coach modes)
- `RetrievedChunk` dataclass added to `ollama.py` for type-safe chunk representation
- All imports verified: no circular dependencies between cache.py, retrieval.py, and ollama.py
