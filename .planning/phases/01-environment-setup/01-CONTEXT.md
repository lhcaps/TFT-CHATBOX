# Phase 1: Environment Setup - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the complete development environment: Ollama running natively on Windows, Supabase local CLI with Postgres + pgvector, Docker Compose for backend + frontend + n8n, and the full database schema. This phase produces a fully operational local stack with zero code written.

</domain>

<decisions>
## Implementation Decisions

### Ollama setup
- **D-01:** Ollama runs **native on Windows** (not containerized) — GPU passthrough friction in Docker
- **D-02:** Models: `qwen3:8b` (chat) + `qwen3-embedding:4b` (embedding), both pulled via `ollama pull`
- **D-03:** Ollama API at `http://localhost:11434` (default)
- **D-04:** `keep_alive: "15m"` set as default to prevent cold-start lag

### Supabase setup
- **D-05:** Supabase local CLI (`npx supabase start`) — NOT in Docker Compose
- **D-06:** Postgres at port **54322**, Studio dashboard at **54323**
- **D-07:** Connection string: `postgresql://postgres:postgres@localhost:54322/postgres`

### Docker Compose
- **D-08:** Docker Compose manages: `backend` + `frontend` + `n8n` only
- **D-09:** Ollama and Supabase accessed via `host.docker.internal` (Windows)
- **D-10:** n8n pinned to version tag (e.g., `1.85`) to avoid breaking changes

### Database schema
- **D-11:** Four tables: `chat_sessions`, `chat_messages`, `documents`, `document_chunks`
- **D-12:** HNSW index on `document_chunks.embedding` with `vector_cosine_ops`
- **D-13:** GIN index on `document_chunks.fts` (full-text search)
- **D-14:** `hybrid_search_chunks()` SQL function with RRF (semantic_weight=2, full_text_weight=1)
- **D-15:** Embedding dimension: **1024** (HNSW max 2000, Ollama configurable)

### Windows considerations
- **D-16:** All Python scripts use `pathlib.Path` — no hardcoded slashes
- **D-17:** `.gitattributes` with `*.py text eol=lf` — prevent CRLF issues
- **D-18:** Windows long path support enabled via registry key
- **D-19:** Environment variables in `.env` file (not shell-specific syntax)

### Healthcheck
- **D-20:** GET `/health` checks both Ollama (`/api/tags`) and Supabase connectivity
- **D-21:** Returns JSON: `{"ollama": "healthy|unreachable", "database": "healthy|unreachable"}`

### Claude's Discretion
- Exact `m` and `ef_construction` values for HNSW index (defaults are fine)
- How to structure Docker volume mounts on Windows (use forward slashes)
- Specific Python package manager (pip vs uv) — pip is fine for MVP
- Supabase CLI migration file format and naming convention

</decisions>

<canonical_refs>
## Canonical References

### Design specification
- `deep-research-report.md` — Full architecture, stack decisions, SQL schema, and pitfall warnings

### Research findings
- `.planning/research/STACK.md` — Ollama configuration, pgvector HNSW settings, Docker Compose setup
- `.planning/research/PITFALLS.md` — Windows path issues, GPU detection, CRLF line endings, Supabase port conflicts
- `.planning/research/ARCHITECTURE.md` — Component breakdown, port assignments, build order

### Project requirements
- `.planning/REQUIREMENTS.md` — FOUND-01 to FOUND-04, DB-01 to DB-06, POLY-05
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, dependencies

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing code — greenfield project. All files are created fresh in this phase.

### Established Patterns
- None — first phase establishes all patterns.

### Integration Points
- Ollama ↔ Docker: `OLLAMA_BASE_URL=http://host.docker.internal:11434` in Docker Compose
- Supabase ↔ Docker: `DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres`
- `.env` file is the single source of truth for all environment variables

</code_context>

<specifics>
## Specific Ideas

- GPU must be verified BEFORE anything else — run `ollama ps` and confirm `size_vram > 0`
- Port 54322 must be verified free before `supabase start`
- Supabase CLI requires Docker Desktop running in background

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 1 decisions are made.

</deferred>

---

*Phase: 01-environment-setup*
*Context gathered: 2026-04-22*
