# Architecture Research: TFT Local Copilot

**Researched:** 2026-04-22
**Confidence:** HIGH (verified against current patterns and documentation)

---

## Component Breakdown

### 1. React Frontend (Chat UI)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | User interaction, message display, streaming token rendering |
| **Boundaries** | Does NOT handle RAG logic, embedding, or LLM inference |
| **Tech** | React 18+ / Vite 5+ / Tailwind CSS 4+ |
| **Build order** | Phase 3 (after backend skeleton, before RAG integration) |

**Key architectural decisions:**

- Uses `fetch` + `ReadableStream.getReader()` for SSE consumption (not `EventSource` — requires POST with body)
- Parse SSE events manually: `event:` and `data:` line parsing
- UI state: messages array, loading state, abort controller for cancellation
- Dark mode via Tailwind `dark:` variants
- Single-user, no auth — localStorage for session persistence only

```tsx
// Simplified streaming pattern
const reader = res.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  // Parse SSE events from buffer
}
```

---

### 2. FastAPI Backend (Orchestration Layer)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Request orchestration, session management, RAG pipeline, SSE streaming |
| **Boundaries** | Does NOT run models — delegates to Ollama; does NOT store chunks — queries Supabase |
| **Tech** | FastAPI / Pydantic / httpx / asyncpg |
| **Build order** | Phase 2 (core), Phase 4 (RAG) |

**Route responsibilities:**

| Route | Purpose | Calls |
|-------|---------|-------|
| `GET /health` | System health check | Ollama `/api/tags`, Supabase connection |
| `POST /api/sessions` | Create chat session | Supabase |
| `GET /api/sessions` | List sessions | Supabase |
| `POST /api/chat/stream` | Streaming chat | Ollama `/api/chat` + optional retrieval |
| `POST /api/search` | Debug retrieval | Hybrid search SQL |
| `POST /api/ingest/*` | Trigger ingestion | Ollama `/api/embed`, Supabase |

**SSE streaming implementation:**

- Ollama returns NDJSON stream via `/api/chat` with `stream: true`
- Backend transforms to SSE format: `event: token\ndata: {...}\n\n`
- Frontend consumes via `ReadableStream`, parses event lines

```python
async def gen():
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", ollama_url, json=payload) as r:
            async for line in r.aiter_lines():
                chunk = json.loads(line)
                delta = chunk.get("message", {}).get("content", "")
                if delta:
                    yield sse("token", {"delta": delta})
                if chunk.get("done"):
                    yield sse("done", {"usage": chunk.get("usage", {})})
```

---

### 3. Ollama (Local Inference Engine)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Text generation (chat model), embedding generation (embedding model) |
| **Boundaries** | Does NOT manage sessions, chunks, or orchestration |
| **Tech** | Ollama native Windows (NOT containerized) |
| **Build order** | Phase 1 (prerequisite) |

**Why native (not containerized) on Windows:**

- GPU passthrough requires NVIDIA Container Toolkit + WSL2 configuration
- Native Windows Ollama directly accesses GPU without Docker friction
- API remains identical: `http://localhost:11434`

**Model configuration for RTX 4070 Ti SUPER 16GB:**

| Model | Role | VRAM | Context |
|-------|------|------|---------|
| `qwen3:8b` | Chat default | ~5.2GB | 4K–8K |
| `qwen3-embedding:4b` | Embedding | ~2.5GB | 40K |
| `gemma3:12b` | Coach (optional) | ~8.1GB | 128K |

**Critical settings:**

- `keep_alive: "15m"` — prevents model unloading between requests
- `num_ctx: 8192` — reasonable context for TFT queries
- Check `ollama ps` to verify GPU usage (look for `size_vram` > 0)

---

### 4. Supabase Local (Database + Vector Store)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Persistent storage, hybrid search (full-text + semantic) |
| **Boundaries** | Does NOT run inference or orchestrate requests |
| **Tech** | Supabase local CLI / PostgreSQL / pgvector / HNSW |
| **Build order** | Phase 1 (setup), Phase 4 (RAG tables) |

**Why Supabase local CLI over Docker:**

- Single command setup: `npx supabase init && supabase start`
- Includes pgvector extension with HNSW support
- Built-in dashboard at `localhost:54323`
- No Docker networking complexity with host services

**Port mapping (default):**

| Service | Port |
|---------|------|
| Postgres | 54322 |
| Studio | 54323 |
| API | 54321 |

---

### 5. Ingestion Pipeline (Python Scripts)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Document processing, chunking, embedding, storage |
| **Boundaries** | Does NOT handle chat requests or user sessions |
| **Tech** | Python / asyncpg / httpx |
| **Build order** | Phase 4 (after RAG tables exist) |

**Ingestion sources:**

| Source | Format | Processing |
|--------|--------|------------|
| Obsidian Vault | Markdown | Heading-based section split + fixed-size chunk |
| TFT Static Data | JSON | Normalize to internal schema |
| Patch Notes | Markdown/JSON | Hash-based incremental update |

---

## Data Flow

### Chat Request Flow (Normal Mode)

```
User → [Frontend] → POST /api/chat/stream
                           │
                           ▼
                     [FastAPI Backend]
                           │
              ┌────────────┴────────────┐
              │                         │
         (Normal)                   (RAG/Coach)
              │                         │
              ▼                         ▼
     [Build Prompt]          [Hybrid Search]
              │                         │
              │                         ▼
              │                   [Rerank + Filter]
              │                         │
              │                         ▼
              └────────────┬────────────┘
                           ▼
                    [Ollama /api/chat]
                           │
              ┌────────────┴────────────┐
              │                         │
         (Stream tokens)            (done: true)
              │                         │
              ▼                         ▼
     [SSE to Frontend]         [Store message]
              │                         │
              ▼                         ▼
     [Render tokens]           [Supabase]
```

### RAG Query Flow

```
User Query
    │
    ▼
[Frontend] ── POST /api/chat/stream ──► [FastAPI]
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │                                                 │
               (Normal)                                        (RAG/Coach)
                    │                                                 │
               Skip RAG                                           │
                    │                                               ▼
                    │                                    [Ollama /api/embed]
                    │                                               │
                    │                                    (query_embedding)
                    │                                               │
                    │                                               ▼
                    │                                    [hybrid_search_chunks()]
                    │                                               │
                    │                            ┌─────────────────┴─────────────────┐
                    │                            │                                   │
                    ▼                            ▼                                   ▼
            [Continue]              [Full-text rank]              [Semantic rank]
                                        │                                   │
                                        └───────── RRF Merge ───────────────┘
                                                    │
                                                    ▼
                                           [Top 6-8 chunks]
                                                    │
                                                    ▼
                                        [Context Assembly + Prompt]
                                                    │
                                                    ▼
                                        [Ollama /api/chat with context]
```

### Ingestion Flow

```
[Source Files]
    │
    ├─► Obsidian Markdown ──► Python Ingest
    │                              │
    │                         [Parse Frontmatter]
    │                              │
    │                         [Split by Headings]
    │                              │
    │                         [Fixed-size Chunks + Overlap]
    │                              │
    │                         [Batch Embed (16 chunks)]
    │                              │
    │                         [Upsert to Supabase]
    │
    └─► TFT Static JSON ──► Python Ingest
                               │
                          [Normalize Schema]
                               │
                          [Generate Markdown]
                               │
                          [Continue: Split → Embed → Store]
```

---

## Ingestion Pipeline

### Chunking Strategy

**Recommendation: Heading-based split + fixed-size with overlap**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk size | 2000 chars | ~500 tokens, preserves semantic coherence |
| Overlap | 500 chars | 25% overlap maintains context across boundaries |
| Split by | Headings (# to ##) first | Keeps related content together |

**Processing pipeline:**

```python
# 1. Walk markdown files (skip .obsidian/)
def walk_markdown_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.md"):
        if ".obsidian" not in p.parts:
            yield p

# 2. Split by heading hierarchy
sections = split_by_headings(markdown)  # [(heading, body), ...]

# 3. Fixed-size chunks with overlap within each section
chunks = fixed_chunks(body, chunk_chars=2000, overlap=500)

# 4. Batch embed (16 at a time for 16GB VRAM)
vectors = await embed_batch(client, texts, dimensions=1024)

# 5. Upsert to Supabase with hash-based deduplication
```

### Batch Embedding

```python
# Ollama supports array input for embedding
response = await client.post(
    f"{OLLAMA_BASE_URL}/api/embed",
    json={
        "model": "qwen3-embedding:4b",
        "input": ["chunk 1", "chunk 2", "...16 chunks"],
        "dimensions": 1024,
        "truncate": True,
        "keep_alive": "15m",
    }
)
embeddings = response.json()["embeddings"]  # [[0.1, ...], ...]
```

### Incremental Updates

- Store `source_hash` in `documents` table
- Compare hash before re-embedding
- Delete stale chunks, insert new ones
- Avoids full re-ingestion on minor changes

---

## Build Order Recommendations

### Phase 1: Foundation (Days 1-2)

| Task | Deliverable |
|------|-------------|
| Install Ollama, pull models | `ollama pull qwen3:8b && ollama pull qwen3-embedding:4b` |
| Verify GPU usage | `ollama ps` shows `size_vram` > 0 |
| Supabase local init | `npx supabase init && supabase start` |
| Create database schema | 4 tables: sessions, messages, documents, chunks |
| Verify connection | Health check passes |

**Dependencies:** None — this is the foundation.

---

### Phase 2: Backend Core (Days 2-3)

| Task | Deliverable |
|------|-------------|
| FastAPI skeleton with routes | `/health`, `/api/sessions`, `/api/chat` |
| Ollama integration | Non-streaming chat works |
| Session persistence | Can create, list, retrieve sessions |
| CORS configuration | Frontend can call backend |

**Dependencies:** Ollama running, Supabase running.

---

### Phase 3: Frontend Shell (Day 3)

| Task | Deliverable |
|------|-------------|
| Vite + React scaffold | `npm create vite@latest` |
| Tailwind CSS 4 integration | `@import "tailwindcss"` in CSS |
| Chat shell UI | Messages display, input sends |
| SSE streaming | Tokens appear in real-time |
| Abort controller | Stop generation works |

**Dependencies:** FastAPI backend with `/api/chat/stream`.

---

### Phase 4: RAG Integration (Days 4-5)

| Task | Deliverable |
|------|-------------|
| Hybrid search SQL function | `hybrid_search_chunks()` with RRF |
| Ingest script for Obsidian | Markdown → chunks → embeddings → Supabase |
| RAG mode in chat | Context injected into prompt |
| Coach mode | Multi-line-of-play prompts |
| Citation tracking | Sources stored with messages |

**Dependencies:** Database schema, Ollama embedding model.

---

### Phase 5: Automation + Polish (Days 6-7)

| Task | Deliverable |
|------|-------------|
| n8n workflows | Scheduled ingest, patch monitoring |
| ngrok webhook | External triggers work |
| Error handling | Ollama fallback, connection retry |
| Smoke testing | 20 test queries pass |
| Documentation | Setup/run instructions |

**Dependencies:** All components working individually.

---

## Platform-Specific Considerations

### Windows + Docker Networking

**Critical issue:** `host.docker.internal` may not resolve on Windows in some configurations.

**Troubleshooting path:**

1. **Verify service listens on `0.0.0.0`**, not `127.0.0.1`:
   ```bash
   # Ollama binds to localhost by default
   # Check: curl http://localhost:11434/api/tags
   ```

2. **If `host.docker.internal` fails**, use `extra_hosts` in Docker Compose:
   ```yaml
   services:
     backend:
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```

3. **Alternative:** Use LAN IP directly (find via `ipconfig`):
   ```yaml
   OLLAMA_BASE_URL: http://10.0.0.1:11434
   DATABASE_URL: postgresql://postgres:postgres@10.0.0.1:54322/postgres
   ```

**Port conflicts to watch:**

| Port | Common Conflict |
|------|-----------------|
| 54322 | Supabase Postgres |
| 54323 | Supabase Studio |
| 5678 | n8n |
| 11434 | Ollama API |

---

### GPU Routing

**Verify Ollama uses GPU:**

```bash
ollama ps
# Look for: size_vram > 0, Processor: NVIDIA
```

**If Ollama falls back to CPU:**

1. Check NVIDIA drivers: `nvidia-smi`
2. Verify CUDA: Ollama requires CUDA 12.x on Windows
3. Restart Ollama service after driver updates

**Multi-GPU selection** (if applicable):
```bash
# Specify GPU for session
OLLAMA_NUM_PARALLEL=1 ollama run qwen3:8b
```

---

### Supabase Local CLI Quirks

| Issue | Solution |
|-------|----------|
| `supabase start` hangs | Check Docker Desktop is running |
| Port already in use | `supabase stop` then restart, or change ports |
| Migrations not applied | `supabase db push` explicitly |
| Reset everything | `supabase stop --backup && supabase start` |

---

## Error Handling Patterns

### Ollama Failures

**Scenario:** Ollama is down or model fails to load.

```python
async def chat_with_fallback(req: ChatRequest):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Try primary model
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()
            # Process stream...
    except (httpx.ConnectError, httpx.TimeoutException):
        # Fallback: notify user
        yield sse("error", {"message": "Ollama unavailable"})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # Model not loaded — trigger load
            await client.post(f"{base}/api/pull", json={"name": model})
            # Retry once
```

**Health check pattern:**

```python
@app.get("/health")
async def health_check():
    status = {"ollama": "unknown", "database": "unknown"}
    
    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("http://localhost:11434/api/tags")
            status["ollama"] = "healthy" if r.status_code == 200 else "error"
    except Exception:
        status["ollama"] = "unreachable"
    
    # Check Supabase
    try:
        conn = await asyncpg.connect(database_url)
        await conn.fetchval("SELECT 1")
        await conn.close()
        status["database"] = "healthy"
    except Exception:
        status["database"] = "unreachable"
    
    return status
```

### Embedding Failures

**Scenario:** Embedding service is slow or fails mid-batch.

```python
async def embed_with_retry(client, texts, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await embed_batch(client, texts)
        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Database Connection Pool

```python
# In db.py
pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
        )
    return pool

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None
```

---

## Deployment Model

### Local Distribution Options

| Approach | Pros | Cons |
|----------|------|------|
| **Script-based** | Simple, transparent | Manual setup |
| **Docker Compose** | Reproducible | GPU passthrough friction |
| **Executable installer** | User-friendly | Complex packaging |

### Recommended: Hybrid Approach

**For MVP development:** Use the existing Docker Compose for backend + n8n, with Ollama and Supabase as host services.

**For distribution:**

1. **Documentation-first:** Clear setup script that:
   - Installs Ollama (downloads and runs installer)
   - Pulls models
   - Starts Supabase local
   - Runs Docker Compose for app services

2. **Optional packaging:**
   - Python backend: `pyinstaller` or similar
   - Frontend: `vite build` produces static files
   - Bundle as `.zip` with start scripts

### Startup Sequence

```bash
# 1. Start Ollama (Windows service or manual)
ollama serve

# 2. Start Supabase local
cd supabase && npx supabase start

# 3. Start Docker services
docker compose up

# 4. Frontend (dev mode)
cd apps/frontend && npm run dev
```

### Environment Configuration

```bash
# .env file in project root
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
ALLOWED_ORIGINS=http://localhost:5173
OBSIDIAN_VAULT_PATH=C:/Users/ADMIN/Vaults/TFT
EMBEDDING_MODEL=qwen3-embedding:4b
EMBEDDING_DIMENSIONS=1024
CHAT_MODEL=qwen3:8b
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER MACHINE                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      HOST SERVICES                        │  │
│  │                                                            │  │
│  │   ┌─────────────┐         ┌──────────────────────────┐   │  │
│  │   │   Ollama    │         │    Supabase Local CLI    │   │  │
│  │   │  (Native)   │         │  ┌────────────────────┐  │   │  │
│  │   │             │         │  │    PostgreSQL     │  │   │  │
│  │   │ 11434/tcp   │         │  │  + pgvector/HNSW  │  │   │  │
│  │   │ GPU: RTX    │         │  └────────────────────┘  │   │  │
│  │   │ 4070 Ti     │         │  54322/tcp (Postgres)   │   │  │
│  │   │ SUPER 16GB  │         │  54323/tcp (Studio)     │   │  │
│  │   └─────────────┘         └──────────────────────────┘   │  │
│  │            │                         ▲                  │  │
│  └────────────┼─────────────────────────┼──────────────────┘  │
│               │                         │                      │
│               │ host.docker.internal     │                      │
│               │ or localhost             │                      │
│               ▼                         │                      │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                   DOCKER SERVICES                           ││
│  │                                                            ││
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   ││
│  │   │   Backend    │  │   Frontend   │  │     n8n      │   ││
│  │   │   FastAPI    │  │  React/Vite  │  │  Automation  │   ││
│  │   │   :8000      │  │    :5173     │  │    :5678     │   ││
│  │   └──────┬───────┘  └──────────────┘  └──────┬───────┘   ││
│  │          │                                    │          ││
│  └──────────┼────────────────────────────────────┼──────────┘│
│             │                                    │             │
│             │ http://localhost:8000              │             │
│             │ http://localhost:5173             │             │
│             ▼                                    ▼             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      BROWSER                                ││
│  │              http://localhost:5173                          ││
│  │              (Chat UI - User Facing)                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      FILE SYSTEM                            │  │
│  │                                                            │  │
│  │   ┌─────────────────────────────────────────────────┐    │  │
│  │   │              Obsidian Vault                      │    │  │
│  │   │         (Markdown notes - Read by ingest)        │    │  │
│  │   └─────────────────────────────────────────────────┘    │  │
│  │                                                            │  │
│  │   ┌─────────────────────────────────────────────────┐    │  │
│  │   │              TFT Static Data                     │    │  │
│  │   │    (JSON - Champions, Items, Traits, Augments)   │    │  │
│  │   └─────────────────────────────────────────────────┘    │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quality Gates

| Gate | Status | Evidence |
|------|--------|----------|
| Components clearly defined with boundaries | ✅ | Section 1: Component Breakdown |
| Data flow direction explicit | ✅ | Section 2: Data Flow diagrams |
| Build order implications noted | ✅ | Section 4: Build Order Recommendations |
| Windows-specific gotchas identified | ✅ | Section 5: Platform-Specific Considerations |
| Error handling patterns documented | ✅ | Section 6: Error Handling Patterns |
| Deployment model specified | ✅ | Section 7: Deployment Model |

---

## Sources

- [Ollama Documentation](https://github.com/ollama/ollama) — API, streaming, embedding
- [Supabase pgvector](https://supabase.com/docs/guides/database/postgres/vector) — HNSW configuration
- [pgvector Hybrid Search](https://dev.to/lpossamai/building-hybrid-search-for-rag-combining-pgvector-and-full-text-search-with-reciprocal-rank-fusion-6nk) — RRF implementation
- [Docker Desktop Networking](https://docs.docker.com/desktop/features/networking/) — host.docker.internal behavior
- [RAG Chunking Strategies 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag) — Chunking recommendations
