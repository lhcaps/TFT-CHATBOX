# Pitfalls Research: TFT Local Copilot

**Project:** TFT Local Copilot
**Researched:** 2026-04-22
**Confidence:** HIGH (based on deep-research-report.md and known technology patterns)

## Executive Summary

This document catalogs common pitfalls across the TFT Local Copilot stack: Ollama integration, pgvector/HNSW on Windows, React SSE consumption, RAG chunking, Supabase local, n8n/ngrok, Windows platform quirks, and TFT policy compliance. Each pitfall includes warning signs, prevention strategies, and phase mapping to guide when to address them during development.

---

## Ollama Integration

### GPU Not Being Used (CPU Fallback)

- **Warning signs:**
  - `ollama ps` shows `Processor: CPU` instead of NVIDIA/AMD
  - VRAM usage stays near zero during inference
  - Response latency 10-20x slower than expected
  - Logs show warnings about CUDA not available

- **Prevention:**
  - Verify CUDA drivers installed: `nvidia-smi`
  - Check Ollama version supports GPU: `ollama -v` (0.5+ has better GPU detection)
  - Set `CUDA_VISIBLE_DEVICES=0` environment variable
  - On Windows, ensure NVIDIA driver version is 535+ for best compatibility
  - Add model explicitly with GPU flag: `OLLAMA_GPU_OVERHEAD=0 ollama run qwen3:8b`

- **Phase:** Phase 1 (Environment Setup) — verify GPU works before anything else

### Context Overflow / Token Limit Hit

- **Warning signs:**
  - Responses truncate abruptly mid-sentence
  - API returns `model context length exceeded` error
  - `eval_count` in response stats near `num_ctx` limit
  - Final chunks of conversation seem "forgotten"

- **Prevention:**
  - Set `num_ctx: 8192` explicitly in API calls (Ollama default is 4096)
  - Implement conversation history pruning: keep only last N messages or trim when exceeding ~80% of context
  - Store older messages in DB, fetch only relevant context for long conversations
  - Monitor `prompt_eval_count` and `eval_count` in streaming responses
  - For Coach mode specifically, limit context to 2-3 recent turns + system prompt + retrieved context

- **Phase:** Phase 2-3 (Backend & Chat) — implement sliding window for long conversations

### Streaming Mismatch (SSE Format Confusion)

- **Warning signs:**
  - Frontend receives garbled/incomplete tokens
  - `aiter_lines()` yields empty strings or malformed JSON
  - Chat "jumps" rather than streams smoothly
  - `done` event never fires

- **Prevention:**
  - Ollama `/api/chat` with `stream: true` returns NDJSON lines
  - Each line is a complete JSON object ending with `\n`
  - Parse line-by-line with `json.loads(line.strip())`
  - Handle `done: true` chunk explicitly to capture final stats
  - Never assume chunks are complete JSON — they arrive incrementally
  - Test with `curl` first: `curl http://localhost:11434/api/chat -d '{"model":"qwen3:8b","messages":[{"role":"user","content":"hi"}],"stream":true}'`

- **Phase:** Phase 3 (Streaming Chat) — this is the core streaming implementation phase

### Model Not Loaded (keep_alive Too Short)

- **Warning signs:**
  - First request after idle period takes 30-60 seconds
  - Subsequent requests are instant
  - `ollama ps` shows model unloaded between requests
  - High `load_duration` in usage stats

- **Prevention:**
  - Set `keep_alive: "15m"` in streaming request to keep model in VRAM
  - Use `OLLAMA_KEEP_ALIVE=15m` environment variable for default
  - For batch/infrastructure tasks, use shorter `keep_alive` to free VRAM
  - Balance: 15min keep_alive with 2 models = ~13GB VRAM (qwen3:8b + embedding)
  - On 16GB VRAM, 2 models + 1GB buffer = safe limit

- **Phase:** Phase 2 (Backend Setup) — configure keep_alive before streaming tests

### Docker Container Can't Reach Native Ollama

- **Warning signs:**
  - FastAPI container returns "Connection refused" to `localhost:11434`
  - Works from host, fails from container
  - `curl` inside container times out

- **Prevention:**
  - Use `host.docker.internal` instead of `localhost` when calling Ollama from Docker
  - Docker Compose config: `OLLAMA_BASE_URL: http://host.docker.internal:11434`
  - Windows: `host.docker.internal` resolves to host machine IP
  - Linux: May need `--add-host=host.docker.internal:host-gateway` in docker-compose
  - Alternative: Run FastAPI on host (not containerized) while only n8n is containerized

- **Phase:** Phase 1 (Environment Setup) — verify Docker-to-Ollama connectivity early

### Embedding Dimension Mismatch

- **Warning signs:**
  - pgvector throws "dimension mismatch" error on insert
  - Embedding vector has 3840 dims but column expects 1024
  - Some models default to high dimensions (e.g., nomic-embed-text at 768, but qwen3-embedding at 1024+)

- **Prevention:**
  - Always specify `dimensions: 1024` in Ollama `/api/embed` request
  - Verify embedding model supports configurable dimensions: `ollama show qwen3-embedding:4b`
  - Create pgvector column with exact dimension: `vector(1024)` not `vector`
  - Document embedding configuration in `.env` and verify on startup

- **Phase:** Phase 4 (RAG Pipeline) — verify dimension configuration before first ingest

---

## pgvector / Database

### HNSW Index Dimension Exceeded (2000 Limit)

- **Warning signs:**
  - `ERROR: cannot create index due to excessive vector length`
  - Index creation fails silently with default `m`/`ef_construction` settings
  - Some vectors accepted, others fail randomly

- **Prevention:**
  - Hard limit: HNSW index in pgvector supports maximum **2000 dimensions**
  - Use **1024 dimensions** for all embeddings (safe margin, good quality)
  - If you need higher quality, consider 1536 dims (still under 2000 limit)
  - Never exceed 2000 — this is a hard constraint, not a recommendation
  - Add validation in ingest pipeline: reject embeddings with wrong dimensions

- **Phase:** Phase 4 (RAG Pipeline) — set dimensions correctly before schema migration

### Index Creation Fails on Large Datasets

- **Warning signs:**
  - `CREATE INDEX` command hangs indefinitely
  - Postgres consumes 100% CPU for hours
  - Index build fails with "out of memory" on large tables
  - Initial embedding insert works, but search is slow

- **Prevention:**
  - Build HNSW index after bulk insert completes, not during
  - Set `m` (connections per layer) and `ef_construction` to reasonable defaults: `m=16, ef_construction=64`
  - For < 100K chunks, default HNSW is fast (< 5 minutes)
  - For larger datasets, consider building index with `concurrently` option or batching
  - Monitor memory: HNSW builds in memory proportional to `m * ef_construction * vector_count`

- **Phase:** Phase 4 (RAG Pipeline) — index tuning after first data load

### Query Performance Degrades with Data Growth

- **Warning signs:**
  - Search queries take > 500ms as chunk count increases
  - `hybrid_search_chunks` function timeout errors
  - CPU/GPU underutilized but latency high (DB bottleneck)

- **Prevention:**
  - HNSW query uses `ef_search` parameter — set to 40-100 for balance
  - Add `LIMIT` to all queries (e.g., `LIMIT 30`) to cap worst case
  - Partition data by `patch` or `season` metadata, query only current partition
  - Consider adding B-tree index on `metadata->>'patch'` for filtering
  - Monitor with `EXPLAIN ANALYZE` on slow queries

- **Phase:** Phase 5 (Optimization) — tune after loading real data volume

### Vector Similarity Calculation Wrong (Cosine vs Euclidean)

- **Warning signs:**
  - RAG results don't match semantic expectations
  - Similar concepts score poorly, unrelated items score well
  - Hybrid search weights seem inverted

- **Prevention:**
  - HNSW index must use same operator class as queries: `vector_cosine_ops` for cosine similarity
  - Use `<=>` operator (cosine distance) not `<->` (Euclidean) with cosine_ops index
  - Verify `hybrid_search_chunks` uses `<=>` for semantic ranking
  - Test with known queries: "tank items" should return items, not champions

- **Phase:** Phase 4 (RAG Pipeline) — verify query operators match index operators

### Supabase Local CLI Port Instability

- **Warning signs:**
  - `npx supabase start` fails with "port already in use"
  - Database connects to wrong instance
  - `DATABASE_URL` points to wrong port after machine restart
  - Supabase CLI reports "Docker container not running"

- **Prevention:**
  - Supabase local uses Docker internally — ensure Docker Desktop is running
  - Use `npx supabase status` to verify all services healthy
  - Port 54322 is default for Postgres (configurable in `config.toml`)
  - Set `SUPABASE_DB_PORT` explicitly if changing defaults
  - Don't run multiple Supabase instances — stop before restarting

- **Phase:** Phase 1 (Environment Setup) — document working port configuration

---

## React / Frontend

### SSE Stream Truncation (Incomplete Events)

- **Warning signs:**
  - Last message appears corrupted or incomplete
  - UI shows partial tokens at end of stream
  - `done` event data is missing
  - Sometimes chat works, sometimes shows garbage

- **Prevention:**
  - Use proper SSE parsing: accumulate in buffer, split on `\n\n`
  - Never assume events arrive complete — use streaming TextDecoder
  - Handle partial lines: store incomplete line in buffer for next chunk
  - Extract event name from `event:` line, data from `data:` line
  - Verify `event: done` fires and contains usage statistics

- **Phase:** Phase 3 (Streaming Chat) — this is the core implementation

### ReadableStream Not Being Read Properly

- **Warning signs:**
  - `response.body` is null on successful HTTP status
  - `getReader()` throws "ReadableStream is not yet readable"
  - Race condition: trying to read after stream already consumed

- **Prevention:**
  - Check `if (!response.body) return` before calling `getReader()`
  - Only call `getReader()` once per response
  - Handle network errors: wrap in try/catch, check `response.ok`
  - For aborted streams: check `reader.cancel()` completes before cleanup
  - Don't mix `response.text()` with `getReader()` — pick one approach

- **Phase:** Phase 3 (Streaming Chat) — test error paths thoroughly

### AbortController Not Canceling Properly

- **Warning signs:**
  - "Stop" button doesn't immediately stop generation
  - Model continues running after user navigates away
  - `signal.aborted` is true but stream keeps yielding tokens
  - Memory leak from orphaned fetch requests

- **Prevention:**
  - Pass `AbortController.signal` to `fetch()` options
  - On abort: call `reader.cancel()` to stop reading, then `reader.releaseLock()`
  - Clean up state in abort handler: set loading=false, preserve partial message
  - Test abort during middle of long generation
  - Handle abort in cleanup function: `useEffect(() => () => controller.abort(), [])`

- **Phase:** Phase 3 (Streaming Chat) — implement and test abort flow

### React State Updates During Stream Cause Re-render Storms

- **Warning signs:**
  - UI stutters or freezes during streaming
  - 60+ re-renders per message as each token arrives
  - Input field becomes unresponsive

- **Prevention:**
  - Batch state updates or use `flushSync` sparingly
  - Consider updating message state every N tokens, not every token
  - Use `useRef` for streaming buffer, update state on "done" event
  - For long messages: use `requestAnimationFrame` to throttle renders
  - Profile with React DevTools to confirm re-render count

- **Phase:** Phase 3 (Streaming Chat) — optimize if performance issues appear

### CORS Preflight Failure

- **Warning signs:**
  - Browser console: "No 'Access-Control-Allow-Origin' header"
  - OPTIONS request returns 403
  - Works in Postman, fails in browser

- **Prevention:**
  - FastAPI: explicitly allow `http://localhost:5173` (not `*` when credentials involved)
  - Include headers in CORS config: `allow_headers=["*"]`
  - Include methods: `allow_methods=["*"]`
  - For development: verify Vite proxy not conflicting with direct fetch
  - Test with browser DevTools Network tab to see actual CORS headers

- **Phase:** Phase 2 (Backend Setup) — configure CORS before frontend integration

---

## RAG / Chunking

### Semantic Coherence Broken by Fixed-Size Chunking

- **Warning signs:**
  - RAG returns fragments of sentences, not complete thoughts
  - Retrieved chunks contain mid-sentence cuts
  - Context doesn't make sense standalone

- **Prevention:**
  - Split by headings first, then apply size limits within sections
  - Never cut mid-sentence — find nearest sentence or paragraph boundary
  - Preserve heading path as metadata: "Patch Notes > 17.1 > Champion Changes > Darius"
  - For Obsidian: each H1/H2/H3 becomes a potential chunk boundary
  - Aim for 512 tokens (~2000 chars) per chunk as starting point

- **Phase:** Phase 4 (RAG Pipeline) — implement heading-aware chunking

### Chunk Overlap Too Small (Losing Context Across Boundaries)

- **Warning signs:**
  - Queries about "items" return no results even though document has item info
  - Related concepts split across chunks and not retrieved together
  - Answers seem incomplete or miss key context

- **Prevention:**
  - Use 25% overlap between chunks (e.g., 2000 char chunk with 500 char overlap)
  - For game knowledge: overlap should include related metadata (champion name, trait)
  - Log which chunks are retrieved to identify boundary issues
  - Increase overlap for dense content (patch notes > general guides)

- **Phase:** Phase 4 (RAG Pipeline) — tune overlap after first retrieval tests

### Heading-Aware Splitting Fails on Edge Cases

- **Warning signs:**
  - Code blocks get split and broken
  - Tables split across chunks
  - Frontmatter included in chunk content
  - Empty chunks created from blank sections

- **Prevention:**
  - Strip YAML frontmatter before chunking (add to metadata instead)
  - Treat code blocks and tables as atomic units (don't split)
  - Skip empty sections (< 50 chars after trim)
  - Normalize whitespace: `re.sub(r'\n{3,}', '\n\n')` before splitting
  - Add debug logging for edge cases during development

- **Phase:** Phase 4 (RAG Pipeline) — handle edge cases in chunking logic

### Re-ingest Creates Duplicate Chunks

- **Warning signs:**
  - Same document appears multiple times in search results
  - Chunk count grows without bound on re-ingest
  - "document_chunks" table has many orphaned records

- **Prevention:**
  - Always `DELETE FROM document_chunks WHERE document_id = $1` before re-inserting
  - Use `ON CONFLICT` with `source_hash` to skip unchanged documents
  - Compare file hash before processing: only re-embed changed files
  - Add document-level unique constraint on `(source_type, source_path, source_hash)`
  - Clean up orphaned chunks when document is deleted

- **Phase:** Phase 4 (RAG Pipeline) — implement idempotent ingest

### Embedding Batch Size Too Large for VRAM

- **Warning signs:**
  - Ollama returns "CUDA out of memory" during batch embedding
  - Embedding inference slows to crawl with larger batches
  - System becomes unresponsive while embedding runs

- **Prevention:**
  - Start with batch size **16** on 16GB VRAM
  - Monitor VRAM usage: `ollama ps` during embedding
  - Increase batch size only if VRAM headroom exists (16GB - model size - 1GB buffer)
  - For safety: batch size 8-16 is conservative; 24-32 is aggressive
  - Implement retry with smaller batch on OOM error

- **Phase:** Phase 4 (RAG Pipeline) — tune batch size during first large ingest

---

## n8n / Automation

### n8n WEBHOOK_URL Points to Wrong Address

- **Warning signs:**
  - Webhook test fails with "connection refused"
  - n8n shows "localhost:5678" instead of public URL
  - External services can't reach n8n webhook

- **Prevention:**
  - Set `WEBHOOK_URL` environment variable explicitly to ngrok URL
  - After ngrok starts, update n8n: `docker compose up -d --force-recreate n8n`
  - Verify WEBHOOK_URL in n8n: Settings > Settings > URL
  - Use `N8N_PROXY_HOPS=1` when behind ngrok/proxy
  - Check n8n logs for "webhook URL mismatch" warnings

- **Phase:** Phase 6 (Automation) — configure ngrok + n8n integration

### ngrok Free Tier URL Changes on Restart

- **Warning signs:**
  - Webhooks stop working after machine restart
  - n8n shows old ngrok URL, new URL is different
  - "Tunnel not found" errors in n8n logs

- **Prevention:**
  - If using free tier: re-fetch ngrok URL after every tunnel start
  - Script URL refresh: query `http://127.0.0.1:4040/api/tunnels` for public URL
  - Automate n8n recreation: `docker compose up -d --force-recreate n8n` after URL change
  - Consider ngrok paid plan for stable domain if automation is critical
  - Document manual steps if automation fails: n8n UI > Settings > Webhook URL

- **Phase:** Phase 6 (Automation) — implement URL refresh script

### n8n Workflow Doesn't Trigger (Not Published)

- **Warning signs:**
  - Schedule trigger doesn't fire at expected times
  - Manual trigger works, but cron doesn't
  - n8n logs show "workflow not active"

- **Prevention:**
  - Workflows must be **activated** (toggle on) to run on schedule
  - Save AND activate: click "Activate" button or toggle switch
  - Verify workflow shows green "Active" badge
  - Check `GENERIC_TIMEZONE` matches your timezone
  - Test with manual trigger first, then activate for automation

- **Phase:** Phase 6 (Automation) — activate workflows after testing

### n8n Can't Reach Backend Container (host.docker.internal)

- **Warning signs:**
  - n8n HTTP Request node fails with "Could not resolve host"
  - Works from browser, fails from n8n
  - n8n container can't ping host

- **Prevention:**
  - Use `http://host.docker.internal:8000` not `localhost:8000`
  - Ensure Docker Compose network allows DNS resolution
  - If n8n is in compose: use service name `http://backend:8000`
  - For n8n on host (not containerized): use `http://localhost:8000`
  - Verify network: `docker exec tft-n8n curl http://host.docker.internal:8000/health`

- **Phase:** Phase 6 (Automation) — test container networking early

### n8n Timezone Issues (Workflows Run at Wrong Time)

- **Warning signs:**
  - Workflow fires 7 hours off (UTC vs Asia/Ho_Chi_Minh)
  - "Every 4 hours" runs at midnight UTC, not midnight SGT
  - Scheduled tasks arrive during off-hours

- **Prevention:**
  - Set `GENERIC_TIMEZONE=Asia/Ho_Chi_Minh` in docker-compose
  - Set `TZ=Asia/Ho_Chi_Minh` environment variable
  - Verify in n8n: Settings > Settings > Timezone shows correct value
  - Test schedule: set to run "Every 1 hour", verify it fires on the hour you expect
  - Note: n8n's schedule uses server timezone, not your local browser timezone

- **Phase:** Phase 6 (Automation) — configure timezone on initial setup

---

## Windows Platform

### Path Separators in Python Scripts

- **Warning signs:**
  - `FileNotFoundError` on Windows, works on Linux
  - Paths like `/vault/notes` fail on Windows
  - Environment variables with paths cause issues

- **Prevention:**
  - Use `pathlib.Path` for all path operations — handles OS differences
  - Never hardcode `/` or `\` — use `Path("/vault")` or `Path(r"C:\vault")`
  - In Python: `Path(os.getenv("OBSIDIAN_VAULT_PATH"))` works cross-platform
  - For Docker volume mounts: use forward slashes even on Windows (`/vault`)
  - Test on Windows before deployment

- **Phase:** Phase 1 (Environment Setup) — use pathlib throughout codebase

### GPU Detection in Windows Environment

- **Warning signs:**
  - Ollama uses CPU despite NVIDIA GPU present
  - `nvidia-smi` works, but Ollama shows no GPU
  - Different behavior when run from PowerShell vs CMD

- **Prevention:**
  - Install NVIDIA driver (not just CUDA toolkit)
  - Verify: `nvidia-smi` shows GPU, `ollama ps` shows `Processor: NVIDIA`
  - Set `CUDA_VISIBLE_DEVICES=0` if multiple GPUs
  - Run Ollama from admin PowerShell if permission issues
  - Check Windows "Graphics settings" — ensure Ollama has GPU access

- **Phase:** Phase 1 (Environment Setup) — diagnose GPU before building anything

### Environment Variable Differences (PowerShell vs CMD vs Docker)

- **Warning signs:**
  - `echo $env:VAR` works, but `echo %VAR%` fails
  - Docker Compose reads different values than terminal
  - `.env` file works for some services, not others

- **Prevention:**
  - Use `.env` file for all Docker Compose services
  - Document environment setup in README with correct shell syntax
  - PowerShell: `$env:VAR = "value"` (temporary), `setx VAR "value"` (permanent)
  - Use `$_` or `.env` expansion in Compose, not shell variable expansion
  - Test with `docker compose config` to verify values are correct

- **Phase:** Phase 1 (Environment Setup) — document all environment variables

### Long Path Names on Windows

- **Warning signs:**
  - "Path too long" errors on Windows
  - npm/yarn install fails with EACCES or EPERM
  - Git operations fail on nested node_modules

- **Prevention:**
  - Enable Windows long path support: `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force`
  - Or: Registry key `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1`
  - Keep project path short: `D:\Projects\TftCopilot` not `D:\Study\Project\Tft Chatbox`
  - Use `npm config set prefix ~/.npm-global` to shorten npm global paths

- **Phase:** Phase 1 (Environment Setup) — enable long paths early

### Line Endings (CRLF vs LF)

- **Warning signs:**
  - Python scripts fail with "bad interpreter" on Windows
  - Shell scripts fail with "no such file" errors
  - Git shows entire file as changed due to line ending changes

- **Prevention:**
  - Set `.gitattributes`: `* text=auto` and `*.py text eol=lf`
  - Use `core.autocrlf` setting: `git config --global core.autocrlf input`
  - For Docker entrypoint scripts: use LF only
  - On Windows: configure editor to use LF for Python/shell files

- **Phase:** Phase 1 (Environment Setup) — configure git line endings before first commit

---

## TFT Policy Compliance

### Real-Time Overlay or In-Game HUD (Immediate Violation)

- **Warning signs:**
  - Project includes screen capture, overlay injection, or overlay rendering
  - UI appears during active TFT gameplay
  - Claims to provide "live" or "real-time" information

- **Prevention:**
  - **Never build overlay features** for TFT
  - Chat UI must be separate window from game
  - No screen scraping or game state reading
  - Product description should emphasize "pre-game" and "static data" use cases
  - Document compliance: README should state "pre-game analysis tool, not real-time assistant"

- **Phase:** All phases — embed policy compliance in product design from day 1

### Opponent Scouting or Board Tracking (Prohibited)

- **Warning signs:**
  - Features that track opponent units, items, or positions
  - "Enemy board" or "opponent analysis" in feature list
  - Claims about reading or tracking other players' game states

- **Prevention:**
  - Never build features that track opponents
  - Coach mode should only suggest based on user's own state
  - RAG retrieval should exclude "scouting data" or "opponent history"
  - If user asks about opponents, coach should respond: "I don't have access to opponent boards — focus on your own line"

- **Phase:** Phase 5 (Coach Mode) — implement policy guardrails in prompts

### "Dictate Player Decisions" or Command-Style Responses (Gray Area)

- **Warning signs:**
  - Coach mode says "you MUST roll now" instead of "consider rolling if..."
  - Responses frame single option as mandatory
  - No acknowledgment of alternative plays

- **Prevention:**
  - Coach mode prompt: "Always suggest 2-3 lines of play with trade-offs"
  - Include "pivot fallback" in every coach response
  - Frame recommendations as suggestions, not commands
  - Coach should explain reasoning, not just state action
  - Example: "If you roll, you risk econ loss. Alternative: fast 8 for better 4-cost odds"

- **Phase:** Phase 5 (Coach Mode) — test policy compliance in prompt engineering

### Accessing Riot APIs Without Proper Attribution (Policy Violation)

- **Warning signs:**
  - App claims to be "official" or "endorsed by Riot"
  - Riot branding or logos used without permission
  - Violates Riot Developer Guidelines on usage

- **Prevention:**
  - Don't use Riot logos or trademarks without explicit permission
  - Clearly state "unofficial tool, not affiliated with Riot Games"
  - Follow Riot API terms: rate limiting, attribution in responses
  - Use Data Dragon (static data) rather than live API when possible
  - Keep app private/personal use — don't distribute as "Riot-supported"

- **Phase:** Phase 1 (Project Setup) — add disclaimers in UI and README

### Using Player Data Without Consent (Privacy Concern)

- **Warning signs:**
  - App stores match history without user's explicit opt-in
  - Assumes user wants their data collected
  - Shares player data with external services

- **Prevention:**
  - All data stays local by default
  - No telemetry or analytics without user consent
  - If adding match history: explicit "enable" toggle, clear explanation
  - Never send player data to any external service (cloud APIs, etc.)
  - All data in Supabase local, Obsidian vault, and Ollama — all on user's machine

- **Phase:** Phase 1 (Project Setup) — privacy-first design

---

## Phase-Specific Warnings Summary

| Phase | Topic | Critical Pitfall | Mitigation |
|-------|-------|------------------|------------|
| 1 | Environment | GPU not detected | Verify with `ollama ps` early |
| 1 | Environment | Path issues on Windows | Use `pathlib`, enable long paths |
| 2 | Backend | CORS misconfigured | Explicit allow `localhost:5173` |
| 2 | Backend | Ollama unreachable from Docker | Use `host.docker.internal` |
| 3 | Streaming | SSE parsing errors | Buffer accumulation, split on `\n\n` |
| 3 | Streaming | Abort doesn't work | Call `reader.cancel()`, release lock |
| 4 | RAG | Wrong embedding dimensions | Always specify `dimensions: 1024` |
| 4 | RAG | Duplicate chunks on re-ingest | DELETE before INSERT |
| 5 | Coach | TFT policy violations | No real-time, no scouting, suggest options |
| 6 | Automation | ngrok URL change | Script URL refresh on restart |
| 6 | Automation | Workflow not activated | Save AND activate toggle |

---

## Quick Reference: Detection Commands

```powershell
# Ollama GPU check
ollama ps

# Supabase status
npx supabase status

# Database connection test
psql "postgresql://postgres:postgres@localhost:54322/postgres" -c "SELECT 1"

# ngrok tunnel status
curl http://127.0.0.1:4040/api/tunnels

# n8n health
curl http://localhost:5678/healthz

# FastAPI health
curl http://localhost:8000/health

# VRAM usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Ollama Integration | HIGH | Documented patterns, official docs verified |
| pgvector/HNSW | HIGH | Hard limits well-documented, Supabase docs |
| React SSE | MEDIUM | Browser API patterns well-known |
| RAG Chunking | HIGH | Established best practices, TFT-specific considerations |
| n8n/ngrok | HIGH | Common Docker + webhook patterns |
| Windows Platform | HIGH | Windows-specific issues well-documented |
| TFT Policy | HIGH | Based on Riot public policy documentation |

---

*Last updated: 2026-04-22*
