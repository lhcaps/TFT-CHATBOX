# Phase 4: RAG Foundation - Context

**Gathered:** 2026-04-22 (assumptions mode, auto)
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the RAG pipeline end-to-end: Obsidian vault ingestion with chunking + embedding, hybrid search retrieval, and context injection into chat responses. RAG and Coach modes retrieve relevant chunks and emit citation events; Normal mode skips retrieval entirely. Citation display and Coach framing are scope (frontend renders what backend emits).

**Scope:** `POST /api/ingest/obsidian`, `POST /api/search`, hybrid retrieval in chat (`rag` + `coach` modes), citation SSE events, `hybrid_search_chunks` wiring, batch embedding.
**Out of scope:** TFT static data ingestion (Phase 5), n8n automation (Phase 6), streaming citation reveal (v2), retrieval debug panel (v2).

</domain>

<decisions>
## Implementation Decisions

### Retrieval Integration (D-01 to D-03)
- **D-01:** Retrieval happens server-side in `build_messages()` — inject retrieved context as a `context` block before the user message. The `build_messages()` function already exists in `app/routes/chat.py`; modify it to accept a mode and prepend context for `rag`/`coach`.
- **D-02:** Use `hybrid_search_chunks` from `supabase/migrations/0001_initial_schema.sql` — weighted score (0.7 semantic + 0.3 text), already implemented. The `0002_create_function.sql` version references `document_chunks` table (doesn't exist) — ignore it.
- **D-03:** Call `hybrid_search_chunks` via `retrieval.py` **before** streaming begins — retrieve context once, inject into prompt, then stream. Do NOT stream citations mid-generation (emit all citations at stream start before first token).

### Citation Event Format (D-04 to D-05)
- **D-04:** Backend emits `event: citation\ndata: {json}\n\n` for each retrieved chunk before the first token event. Format: `{"citation": {"id": str, "source": str, "heading": str, "text": str, "score": float}}`.
- **D-05:** Frontend SSE parser in `apps/frontend/src/api/chat.ts` already handles `event: citation`. The `useChat.ts` hook wires `onCitation` to accumulate citations on the streaming message. Frontend DID need changes: `Citation` type updated from `{similarity}` to `{heading, score}`, `CitationCard` refactored to show heading + score %, `MessageList` updated to render citation cards (not just a text label).

### Obsidian Ingest (D-06 to D-08)
- **D-06:** Chunking: 2000 char chunks with 500 char overlap. Update `rag_chunk_size: int = 2000` in `config.py`. Update `split_into_chunks()` in `app/utils/markdown.py` to add overlap parameter.
- **D-07:** Batch embedding: 16 chunks per Ollama `/api/embed` request (not `/api/embeddings`). Batch endpoint confirmed working via curl — returns `{"model": "...", "embeddings": [[...], [...]]}`. Update `ingest_obsidian.py` to batch-collect chunks, call `ollama.generate_embeddings()` (array input), then bulk-insert. Add `generate_embeddings()` to `app/services/ollama.py`.
- **D-08:** Incremental re-ingest: hash-based deduplication already in `ingest_obsidian.py` via `content_hash`. When file changes → new hash → re-insert. When file unchanged → skip. No ON CONFLICT needed; existing skip logic is sufficient.

### Prompt Injection (D-09 to D-10)
- **D-09:** Context block format: prepend a special `user`-role message containing the retrieved chunks. Format: `---CONTEXT---\n[1] From: {source} > {heading}\n{chunk_text}\n[2] From: ...\n---CONTEXT---`. The system prompt for `rag` already instructs `[source]` citations — model self-cites.
- **D-10:** Coach mode retrieval: same retrieval path as RAG. Coach prompt already includes "based on their board, available shop, and game state" framing. Retrieval provides Obsidian context as additional grounding. Do NOT add game state — user provides that in their message.

### Search Endpoint (D-11)
- **D-11:** `POST /api/search` endpoint in `app/routes/search.py` (new file) that calls `hybrid_search_chunks` directly and returns top chunks with scores. Used for debugging retrieval quality. Not called by frontend chat flow.

### Chunk Schema Alignment (D-12)
- **D-12:** The `chunks` table (from `0001_initial_schema.sql`) has `source VARCHAR(255)`. The `hybrid_search_chunks` returns `source VARCHAR(255)` and `metadata JSONB`. Store heading path in `metadata` as `{"heading_path": "..."}`. Do NOT alter the table schema — store heading in metadata JSONB.

### Claude's Discretion
- Ollama API endpoint for batch: use `/api/embed` (singular, supports array `input` field) — NOT `/api/embeddings` (plural, single-text only). Verified working via curl — returns `{"model": "...", "embeddings": [[...], [...]]}`.
- `ef_search` for HNSW: default 40 is fine. Do not tune unless retrieval latency > 500ms.
- Whether to use Ollama's native batch embedding or sequential single embeds: batch (D-07) is recommended — reduces HTTP overhead. Single embeds are the fallback if batch API is unreliable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project context
- `.planning/PROJECT.md` — Vision, stack, constraints, TFT policy compliance
- `.planning/REQUIREMENTS.md` — RAG-01 to RAG-07, PROMPT-01 to PROMPT-03
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria, dependencies
- `.planning/STATE.md` — Accumulated context, locked decisions from Phase 1-3

### Prior phase context
- `.planning/phases/02-backend-core/02-CONTEXT.md` — Backend decisions (SSE format, mode system, history window)
- `.planning/phases/03-frontend-chat/03-CONTEXT.md` — Frontend decisions (SSE parsing, session state, hook architecture)

### Existing code (read before implementing)
- `apps/backend/app/routes/chat.py` — `build_messages()` function to modify for context injection
- `apps/backend/app/services/retrieval.py` — `retrieve_chunks()` to replace with `hybrid_search_chunks` call
- `apps/backend/app/services/ollama.py` — `OllamaService` to add `generate_embeddings()` for batch
- `apps/backend/scripts/ingest_obsidian.py` — existing ingest to update for batch + overlap
- `apps/backend/app/utils/markdown.py` — `split_into_chunks()` to add overlap parameter
- `apps/backend/app/config.py` — `rag_chunk_size` default to update to 2000
- `apps/frontend/src/hooks/useChat.ts` — `onCitation` handler wires citations to streaming message
- `apps/frontend/src/api/chat.ts` — SSE parser already handles `citation` event type
- `supabase/migrations/0001_initial_schema.sql` — `chunks` table + `hybrid_search_chunks` function

### Research findings
- `.planning/research/STACK.md` — Ollama embedding batch API, `dimensions: 1024`
- `.planning/research/PITFALLS.md` — Phase 4 pitfalls: wrong dims, duplicate chunks, SSE citation timing

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/routes/chat.py` `build_messages()` — modify to prepend context block
- `app/services/retrieval.py` `retrieve_chunks()` — replace inner query with `hybrid_search_chunks` call
- `app/services/ollama.py` `OllamaService.generate_embedding()` — add `generate_embeddings()` for batch
- `scripts/ingest_obsidian.py` — existing file walker, frontmatter extraction, hash dedup — update chunking + batching
- `app/utils/markdown.py` `split_into_chunks()` — add overlap parameter
- `apps/frontend/src/hooks/useChat.ts` `onCitation` — already wired, accumulates citations on the streaming message
- `apps/frontend/src/api/chat.ts` — SSE parser already handles `citation` event type, `extractEvents()` splits on `\n\n`

### Established Patterns
- All async DB calls use `pool.acquire()` context manager pattern
- SSE events: `event: {name}\ndata: {json}\n\n` format (double newline)
- Settings via `pydantic_settings.BaseSettings` with `.env` file
- Repository pattern for DB access

### Integration Points
- Chat route → `build_messages()` (modified) → prepends context for `rag`/`coach`
- `build_messages()` → `retrieval.py` → `hybrid_search_chunks` (SQL function)
- `retrieval.py` → `ollama.py` → generates query embedding
- Ingest route → `ingest_obsidian.py` → batches → bulk insert to `chunks` table
- Stream response → `event: citation` emitted BEFORE first token → frontend `onCitation`

</code_context>

<specifics>
## Specific Ideas

- Context block: `---CONTEXT---\n[1] {source} > {heading}\n{text}\n---CONTEXT---` — simple, model reads it as structured input
- Citation `id`: chunk `id` from DB (primary key)
- Citation `source`: `source` field from `chunks` table (file path)
- Citation `heading`: from `metadata->>'heading_path'` JSONB field
- Citation `text`: `content` field from `chunks` table
- Citation `score`: `similarity` float from `hybrid_search_chunks` result
- Batch size: 16 chunks per embed request (VRAM-safe for 16GB GPU)
- Chunk overlap: 500 chars (25% of 2000-char chunk)

</specifics>

<deferred>
## Deferred Ideas

### Ideas for Future Phases
- TFT static data ingestion (champions, traits, items, augments) — Phase 5 scope
- Streaming citation reveal alongside tokens — Phase v2 (RAG-09)
- Retrieval debug panel showing chunks + scores — Phase v2 (RAG-10)
- Metadata filtering (patch, season) in retrieval — Phase 5 scope (RAG-06)
- Inline citation cards with hover/tap snippets — Phase v2 (RAG-08)
- Heuristic reranking by patch/season priority — Phase v2 (RAG-11)

### Not in Scope
- n8n scheduled ingest — Phase 6 scope
- GPU monitoring in frontend — Phase 7 scope
- Query embedding cache — Phase 7 scope (POLY-01)

### Bugfixes Found During Implementation
- `apps/backend/app/routes/ingest.py`: fixed `app.scripts.*` → `scripts.*` import paths (correct relative import from `app/` module), added `rag_chunk_overlap` parameter to `ingest_vault()` call.
- `apps/frontend/src/api/types.ts`: updated `Citation` interface from `{similarity}` to `{heading, score}` to match backend emission format.

</deferred>

---

*Phase: 04-rag-foundation*
*Context gathered: 2026-04-22*
*Status: Ready for planning*
