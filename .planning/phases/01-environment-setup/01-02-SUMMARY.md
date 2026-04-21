# Phase 01-02 Summary: Database Schema Migration

**Phase:** 01-02
**Executed:** 2026-04-22
**Status:** COMPLETED

---

## Objectives

Create the complete database schema for the TFT Local Copilot including all four tables, indexes, and the hybrid search function.

---

## Tasks Completed

### Task 1: Create Database Migration File ✅

**File:** `supabase/migrations/0001_initial_schema.sql`

Created the migration file containing:
- Extensions: `pgcrypto`, `vector`
- 4 tables: `chat_sessions`, `chat_messages`, `documents`, `document_chunks`
- All required indexes (B-tree, GIN, HNSW)
- Table constraints and check constraints

**Additional file:** `supabase/migrations/0002_create_function.sql`
- Contains the `hybrid_search_chunks()` function with RRF implementation

### Task 2: Push Schema to Supabase ✅

**Status:** Schema was already present in the database

The schema was already applied to the Supabase local instance. All tables, indexes, and the function were verified to exist.

### Task 3: Verify Schema Applied ✅

All verifications passed:

| Verification | Result |
|--------------|--------|
| Tables exist | 4 tables: chat_sessions, chat_messages, documents, document_chunks |
| HNSW index | `document_chunks_embedding_hnsw_idx` using `vector_cosine_ops` |
| GIN index | `document_chunks_fts_idx` on `fts` column |
| Function | `hybrid_search_chunks` with 6 parameters |
| Embedding column | `vector(1024)` dimension confirmed |

---

## Key Schema Details

### Tables

1. **chat_sessions** - Stores chat session metadata
   - Columns: id, title, mode, metadata, created_at, updated_at
   - Mode values: 'normal', 'rag', 'coach'

2. **chat_messages** - Stores individual messages
   - Columns: id, session_id, role, content, citations, usage, created_at
   - Foreign key to chat_sessions with cascade delete

3. **documents** - Document metadata with deduplication
   - Columns: id, source_type, source_path, source_hash, title, season, patch, locale, metadata, raw_markdown, created_at, updated_at
   - Unique constraint on (source_type, source_path, source_hash)

4. **document_chunks** - Chunked content with embeddings
   - Columns: id, document_id, chunk_index, heading_path, content, token_estimate, embedding, metadata, fts, created_at
   - Generated `fts` tsvector column for full-text search
   - Unique constraint on (document_id, chunk_index)

### Indexes

| Index Name | Type | Column/Expression |
|------------|------|------------------|
| chat_messages_session_created_idx | B-tree | (session_id, created_at) |
| document_chunks_document_idx | B-tree | (document_id, chunk_index) |
| document_chunks_fts_idx | GIN | fts |
| document_chunks_embedding_hnsw_idx | HNSW | embedding vector_cosine_ops |

### Hybrid Search Function

```sql
hybrid_search_chunks(
  query_text text,
  query_embedding vector(1024),
  match_count int default 8,
  full_text_weight float default 1,
  semantic_weight float default 2,
  rrf_k int default 50
)
```

Uses Reciprocal Rank Fusion (RRF) to combine:
- Full-text search (weight=1)
- Semantic search with cosine similarity (weight=2)

---

## Security Advisory

The Supabase CLI flagged that Row Level Security (RLS) is disabled on all 4 tables. This is acceptable for a local-first application where all data stays on the user's machine.

**Note:** This is intentional for MVP since:
- No external network exposure
- Single local user
- All data is private

If future phases require network exposure, RLS policies should be added.

---

## Git Commit

```
commit 7dc2cb5
Phase 01-02: Add database schema with tables, indexes, and hybrid_search function

- Created 4 tables: chat_sessions, chat_messages, documents, document_chunks
- Added HNSW index on document_chunks.embedding with vector_cosine_ops
- Added GIN index on document_chunks.fts for full-text search
- Added B-tree indexes for efficient queries
- Created hybrid_search_chunks() function with RRF (semantic_weight=2, full_text_weight=1)
- vector(1024) dimension for embeddings
```

---

## Next Steps

This phase is complete. The database schema is ready for:
- Phase 02: Backend API integration
- Phase 04: RAG Foundation with embedding ingestion

---

*Generated: 2026-04-22*
