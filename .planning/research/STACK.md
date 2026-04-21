# Stack Research: TFT Local Copilot

**Project:** TFT Local Copilot — local AI chatbot for Teamfight Tactics
**Hardware:** 64GB RAM + RTX 4070 Ti SUPER 16GB VRAM (Windows)
**Models:** qwen3:8b (chat), qwen3-embedding:4b (embedding), gemma3:12b (optional)
**Researched:** 2026-04-22

---

## Frontend Stack

### Recommendation

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework |
| Vite | 6.x | Build tool and dev server |
| Tailwind CSS | 4.x | Utility-first styling |
| TypeScript | 5.x | Type safety |

### Rationale

**React 19 + Vite 6 + Tailwind 4** is the current standard for rapid UI development in 2026. This combination provides:

- **Fast HMR**: Vite's native ESM-based dev server provides sub-second hot module replacement, critical for iterative UI development
- **Tailwind v4 plugin**: `@tailwindcss/vite` is the official Vite integration, configured in two lines
- **No build overhead**: Both React 19 and Vite 6 have optimized production builds with code splitting

**Why NOT create-react-app or CRA**: Deprecated, slow builds, poor TypeScript support. Vite is the community standard.

### Confidence: HIGH

**Sources:**
- [Tailwind CSS v4 + Vite setup guide (DEV Community, 2025)](https://dev.to/imamifti056/how-to-setup-tailwind-css-v415-with-vite-react-2025-updated-guide-3koc)
- [Vite + React + Tailwind YouTube (2026)](https://www.youtube.com/watch?v=vm7UuXcaYMg)

---

## Backend Stack

### Recommendation

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.115+ | Web framework |
| Uvicorn | 0.30+ | ASGI server |
| Pydantic | 2.x | Data validation |
| httpx | 0.28+ | Async HTTP client |
| asyncpg | 0.30+ | Async Postgres driver |
| python-dotenv | 1.x | Environment config |

### Rationale

**FastAPI** is the de facto standard for Python APIs in 2026 because:
- Native async support with `async def` for non-blocking I/O
- Pydantic v2 integration for request/response validation
- Built-in `StreamingResponse` for SSE with proper media type handling

**httpx over requests**: Both support streaming, but `httpx.AsyncClient` is truly async and handles connection pooling better for concurrent requests to Ollama.

**asyncpg over psycopg2**: Your FastAPI backend will handle concurrent requests. `asyncpg` provides non-blocking Postgres access, while `psycopg2` blocks the event loop.

**Why NOT Django**: Overkill for a local copilot. Django's ORM and auth system add complexity with no benefit for a single-user local app.

**Why NOT Flask**: No native async, poor streaming support, manual Pydantic integration required.

### Confidence: HIGH

**Sources:**
- [FastAPI Server-Sent Events documentation](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [FastAPI Streaming Data](https://fastapi.tiangolo.com/advanced/stream-data/)
- [Streaming APIs with FastAPI (Python in Plain English, Oct 2025)](https://python.plainenglish.io/streaming-apis-for-beginners-python-fastapi-and-async-generators-848b73a8fc06)

---

## Ollama Integration

### Recommendation

| Aspect | Setting | Rationale |
|--------|---------|-----------|
| Base URL | `http://localhost:11434` | Native Windows Ollama |
| Chat endpoint | `/api/chat` | Supports streaming, messages array |
| Embed endpoint | `/api/embed` | Batch input support |
| keep_alive | `"15m"` | Balance memory vs. responsiveness |
| Context window | 8192 | Leave headroom for retrieval context |
| Embed dimensions | 1024 | Stay under HNSW 2000-dim limit |

### Rationale

**Native Ollama (not containerized)** on Windows is correct for your hardware because:
- GPU passthrough friction in Docker on Windows
- Direct CUDA access without container overhead
- Ollama Windows native binds to `localhost:11434` automatically

**keep_alive tuning**:
- `"5m"` (default): Model unloads after 5 minutes idle — causes reload lag on resume
- `"15m"`: Good balance for interactive chat — model stays warm during conversation
- `"-1"`: Keep loaded indefinitely — use if chatting frequently
- `"0"`: Unload immediately after request — use when running multiple models

**Embedding dimensions 1024**:
- Ollama's embedding models support flexible output dimensions
- 1024 is well under pgvector's 2000-dimension HNSW limit
- 2048-dim embeddings would require dimensionality reduction or IVFFlat

**Batch embedding**: `/api/embed` accepts array input. Ingest scripts should batch 16-32 chunks per request to reduce HTTP overhead.

### Ollama API Usage

```python
# Chat with streaming
async with httpx.AsyncClient(timeout=None) as client:
    async with client.stream(
        "POST",
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": "qwen3:8b",
            "messages": [{"role": "user", "content": "..."}],
            "stream": True,
            "keep_alive": "15m",
            "options": {"num_ctx": 8192},
        },
    ) as r:
        async for line in r.aiter_lines():
            if line:
                chunk = json.loads(line)
                # Process delta or done
```

```python
# Batch embedding
response = await client.post(
    f"{OLLAMA_BASE_URL}/api/embed",
    json={
        "model": "qwen3-embedding:4b",
        "input": ["text1", "text2", "text3"],
        "dimensions": 1024,
        "truncate": True,
        "keep_alive": "15m",
    },
    timeout=180.0,
)
embeddings = response.json()["embeddings"]  # List[List[float]]
```

### Confidence: HIGH

**Sources:**
- [Ollama API documentation (GitHub)](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Embed API](https://docs.ollama.com/api/embed)
- [Ollama Streaming](https://docs.ollama.com/capabilities/streaming)

---

## Streaming Architecture

### FastAPI SSE Best Practices

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

def sse(event: str, data: dict) -> bytes:
    """Format event as SSE message."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")

@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        async with httpx.AsyncClient(timeout=None) as client:
            # Call Ollama, forward tokens as SSE
            async for line in ollama_stream(client, request):
                if line.get("done"):
                    yield sse("done", {"content": "...", "usage": {...}})
                else:
                    yield sse("token", {"delta": line.get("message", {}).get("content", "")})
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
```

### Critical SSE Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Type` | `text/event-stream` | SSE protocol |
| `Cache-Control` | `no-cache` | Prevent proxy caching |
| `X-Accel-Buffering` | `no` | Disable nginx buffering |

### React SSE Consumption

```typescript
async function sendMessage(text: string) {
  const controller = new AbortController();
  
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
    signal: controller.signal,
  });

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const raw of events) {
      const event = raw.match(/^event: (\w+)/)?.[1];
      const data = raw.match(/^data: (.+)/s)?.[1];
      if (!event || !data) continue;

      const parsed = JSON.parse(data);
      if (event === "token") {
        appendToken(parsed.delta);
      } else if (event === "done") {
        finalizeMessage(parsed);
      }
    }
  }
}
```

### Why fetch + ReadableStream (NOT EventSource)

`EventSource` is server-to-client only and requires GET requests. For POST requests with complex body, `fetch + ReadableStream` is the correct pattern.

### Confidence: HIGH

**Sources:**
- [FastAPI SSE official docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [React SSE patterns (Level Up Coding, 2026)](https://levelup.gitconnected.com/react-ai-building-intelligent-web-applications-in-2026-6d412830f705)

---

## Database: Supabase Local CLI

### Recommendation

| Component | Technology | Version |
|-----------|------------|---------|
| Database | Postgres | 16.x (via Supabase) |
| Vector extension | pgvector | 0.8+ |
| CLI tool | Supabase CLI | 2.x |
| Connection | Direct Postgres | Port 54322 |

### Rationale

**Supabase local CLI** is correct because:
- One command `supabase start` launches Postgres + pgvector + dashboard
- pgvector extension included and pre-configured
- No Docker complexity for the database layer
- Dashboard at `localhost:54323` for visual inspection

**Why NOT Docker Compose for Supabase**: Supabase has complex internal architecture (Postgres, Kong, GoTrue, etc.). The CLI abstracts this complexity.

**Connection string for Docker Compose apps**:
```
postgresql://postgres:postgres@host.docker.internal:54322/postgres
```

### Confidence: HIGH

**Sources:**
- [Supabase Local Development docs](https://supabase.com/docs/guides/local-development)
- [pgvector HNSW indexes](https://supabase.com/docs/guides/ai/vector-indexes/hnsw-indexes)

---

## pgvector / HNSW Configuration

### Recommendation

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Extension | `vector` | Core pgvector extension |
| Dimensions | 1024 | Under 2000-dim HNSW limit |
| Index type | HNSW | Default for high recall |
| Operator class | `vector_cosine_ops` | Cosine distance for embeddings |
| `m` | 16 (default) | Connections per layer |
| `ef_construction` | 64 (default) | Build-time candidate list |
| `ef_search` | 100 | Query-time tuning |

### HNSW Index Creation

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
  id bigserial PRIMARY KEY,
  document_id uuid REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index int NOT NULL,
  heading_path text,
  content text NOT NULL,
  embedding vector(1024),  -- Must match embedding model output
  metadata jsonb DEFAULT '{}',
  fts tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(heading_path, '') || ' ' || coalesce(content, ''))
  ) STORED,
  created_at timestamptz DEFAULT now(),
  UNIQUE (document_id, chunk_index)
);

-- HNSW index for semantic search
CREATE INDEX document_chunks_embedding_hnsw_idx
  ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- GIN index for full-text search
CREATE INDEX document_chunks_fts_idx
  ON document_chunks USING gin(fts);
```

### Query-Time Tuning

```sql
-- Per-session tuning for recall vs. speed
SET hnsw.ef_search = 100;  -- Higher = better recall, slower

-- For filtered searches (pgvector 0.8+)
SET hnsw.iterative_scan = 'relaxed_order';
```

### Why HNSW over IVFFlat

| Aspect | HNSW | IVFFlat |
|--------|------|---------|
| Query latency | Consistent | Variable |
| Build time | Slower | Faster |
| Recall | Higher | Lower |
| Memory | Higher | Lower |
| Best for | <10M vectors | >10M vectors |

HNSW is the **default choice** for datasets under 10M vectors. Your knowledge base will be orders of magnitude smaller.

### Confidence: HIGH

**Sources:**
- [pgvector HNSW indexes (Supabase docs)](https://supabase.com/docs/guides/ai/vector-indexes/hnsw-indexes)
- [pgvector performance tips (Crunchy Data)](https://www.crunchydata.com/blog/pgvector-performance-for-developers)
- [Azure pgvector optimization](https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/howto-optimize-performance-pgvector)

---

## Docker Compose Setup

### Recommendation

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ../apps/backend
      dockerfile: Dockerfile
    container_name: tft-backend
    environment:
      APP_ENV: development
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      DATABASE_URL: postgresql://postgres:postgres@host.docker.internal:54322/postgres
      ALLOWED_ORIGINS: http://localhost:5173
    ports:
      - "8000:8000"
    volumes:
      - ../apps/backend:/app
    command: >
      sh -c "pip install -r requirements.txt &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  frontend:
    build:
      context: ../apps/frontend
      dockerfile: Dockerfile
    container_name: tft-frontend
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    ports:
      - "5173:5173"
    volumes:
      - ../apps/frontend:/app
    command: >
      sh -c "npm install && npm run dev -- --host 0.0.0.0"

  n8n:
    image: docker.n8n.io/n8nio/n8n:1.85
    container_name: tft-n8n
    ports:
      - "5678:5678"
    environment:
      N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS: "true"
      GENERIC_TIMEZONE: Asia/Ho_Chi_Minh
      WEBHOOK_URL: ${WEBHOOK_URL:-http://localhost:5678/}
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:

# Note: Ollama runs NATIVE on Windows, NOT in Docker
# Note: Supabase runs via CLI, NOT in Docker
```

### Critical Configuration

| Aspect | Setting | Why |
|--------|---------|-----|
| Ollama access | `host.docker.internal:11434` | Connect to native Windows Ollama |
| Supabase access | `host.docker.internal:54322` | Connect to Supabase local CLI |
| Network mode | Bridge (default) | Don't use `host` mode on Windows |
| Pin n8n version | `1.85` | Avoid breaking changes |

### Why Ollama NOT in Docker

| Approach | Pros | Cons |
|----------|------|------|
| Native Ollama | Direct GPU access, no passthrough | Manual management |
| Ollama in Docker | Isolated, reproducible | GPU passthrough friction on Windows/WSL2 |

For Windows with NVIDIA, native Ollama is the lower-friction path.

### Confidence: HIGH

**Sources:**
- [Docker Compose + Ollama GPU setup](https://www.glukhov.org/llm-hosting/ollama/ollama-in-docker-compose/)
- [Ollama Docker deployment (SitePoint)](https://www.sitepoint.com/ollama-local-llm-production-deployment-docker/)

---

## Windows-Native Toolchain

### Recommendation

| Tool | Purpose | Install |
|------|---------|---------|
| Ollama | LLM inference | `OllamaSetup.exe` from ollama.com |
| Supabase CLI | Database management | `npm i -g supabase` |
| Python | Runtime | python.org or `winget install Python311` |
| Node.js | Frontend tooling | nodejs.org or `winget install OpenJS.NodeJS` |
| n8n | Automation | Docker (via compose) |

### Environment Variables

```powershell
# System-level (or .env file)
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"
$env:OBSIDIAN_VAULT_PATH = "D:\Obsidian\Vault"
$env:EMBEDDING_MODEL = "qwen3-embedding:4b"
$env:CHAT_MODEL = "qwen3:8b"
```

### Confidence: MEDIUM

No major changes in Windows tooling ecosystem. Python 3.11+ and Node 20+ are stable.

---

## What NOT to Use

| Technology | Why Not | Instead |
|------------|---------|---------|
| **Django** | Overkill for single-user local app; complex ORM, auth system unnecessary | FastAPI |
| **create-react-app** | Deprecated; slow builds, poor TS support | Vite |
| **psycopg2** | Blocks async event loop | asyncpg |
| **requests library** | Synchronous only; no true async | httpx |
| **WebSockets for chat** | Overkill for one-way streaming | SSE |
| **EventSource for POST** | GET-only, no request body support | fetch + ReadableStream |
| **IVFFlat (default)** | Lower recall than HNSW for small datasets | HNSW |
| **2048-dim embeddings** | Exceeds HNSW 2000-dim limit | 1024-dim |
| **ollama pull in container** | GPU passthrough friction on Windows | Native Ollama |
| **ngrok for local dev** | Unnecessary complexity; URL changes on restart | Direct localhost |
| **Redis** | Not needed for caching at MVP scale | In-memory LRU |

### Confidence: HIGH

---

## Sources

| Source | Confidence | Last Verified |
|--------|------------|---------------|
| [FastAPI SSE docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) | HIGH | 2026-04 |
| [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md) | HIGH | 2026-04 |
| [pgvector HNSW (Supabase)](https://supabase.com/docs/guides/ai/vector-indexes/hnsw-indexes) | HIGH | 2026-04 |
| [Tailwind + Vite setup (DEV)](https://dev.to/imamifti056/how-to-setup-tailwind-css-v415-with-vite-react-2025-updated-guide-3koc) | MEDIUM | 2025 |
| [Docker + Ollama GPU](https://www.glukhov.org/llm-hosting/ollama/ollama-in-docker-compose/) | MEDIUM | 2025 |
| [pgvector performance (Crunchy)](https://www.crunchydata.com/blog/pgvector-performance-for-developers) | HIGH | 2025 |

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Frontend Stack | HIGH | Well-established React/Vite/Tailwind ecosystem |
| Backend Stack | HIGH | FastAPI is proven for LLM streaming apps |
| Ollama Integration | HIGH | Direct from Ollama official docs |
| SSE Architecture | HIGH | Based on FastAPI official examples |
| pgvector/HNSW | HIGH | Based on Supabase official documentation |
| Docker Compose | MEDIUM | Pattern verified, Windows-specific nuances may vary |
| Windows Toolchain | MEDIUM | General guidance, no major changes in ecosystem |
