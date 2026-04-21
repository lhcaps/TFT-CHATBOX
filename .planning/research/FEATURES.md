# Features Research: TFT Local Copilot

**Domain:** Local AI copilot for Teamfight Tactics (Set 17 Space Gods)
**Researched:** 2026-04-22
**Confidence:** MEDIUM-HIGH (grounded in existing spec + ecosystem patterns)

---

## Table Stakes

Features users expect or they won't use the product. Missing any of these = product feels broken/incomplete.

### Chat UI (Must Have)

| Feature | Why Expected | Complexity | Dependencies | TFT Policy Note |
|---------|--------------|------------|--------------|-----------------|
| **Streaming responses (SSE)** | Users expect real-time token-by-token output; without it, local LLM latency (3-8s) makes the app feel frozen or dead. All modern AI apps (ChatGPT, Claude, Copilot) use streaming. | Low | Backend SSE endpoint, frontend `ReadableStream` reader | Neutral |
| **Mode switching (Normal / RAG / Coach)** | Three distinct use cases need explicit UI toggling; mixing them silently causes confused responses. Users must understand which mode is active. | Low | Prompt templates per mode, session metadata | Neutral |
| **Abort / stop generation** | Long responses from 8B models on complex TFT questions can be irrelevant; users need a way to kill the stream without refreshing. Standard UX pattern. | Low | `AbortController` on frontend, early `return` on backend stream | Neutral |
| **Chat history list** | Users expect to revisit past advice sessions — especially for patch notes and coach analysis. Without it, each conversation is throwaway. | Low | `chat_sessions` table, session listing endpoint | Neutral |
| **Message persistence (reload session)** | After app restart, previous conversations should still be there. This is the baseline expectation for any chat app. | Low | `chat_messages` table, message history endpoint | Neutral |
| **Basic citation display (end-of-response)** | Minimum viable trust signal — shows which document(s) the answer came from. Users won't trust AI advice on game meta without provenance. | Medium | `citations` JSONB in `chat_messages`, citation rendering in UI | Neutral |

### RAG Features (Must Have)

| Feature | Why Expected | Complexity | Dependencies | TFT Policy Note |
|---------|--------------|------------|--------------|-----------------|
| **Obsidian vault ingest (file watcher or on-demand)** | Personal notes are the primary knowledge source; if they don't appear in answers, the RAG mode is useless. | Medium | File system watcher or manual trigger, Python ingest script | Neutral |
| **Hybrid search (vector + full-text)** | Pure vector search misses exact TFT terminology (champion names, trait IDs); pure FTS misses semantic intent. Hybrid is the standard 2026 approach. | Medium | `hybrid_search_chunks()` SQL function, HNSW + GIN indexes | Neutral |
| **Metadata filtering (patch, season)** | TFT meta changes every 2 weeks; stale patch data actively misleads. Users must be able to scope queries to current patch. | Medium | `patch` and `season` columns in `documents` and `document_chunks`, filter in retrieval | Neutral |
| **TFT static data ingestion (champions, traits, items, augments)** | The app's credibility rests on grounding answers in accurate game data. Without it, Coach mode hallucinating item recipes destroys trust. | Medium | `ingest_tft_static.py`, Riot Data Dragon + CommunityDragon sources | Neutral |
| **Chunking strategy (heading + fixed-size with overlap)** | Heading-aware chunks preserve note structure; overlap prevents splitting critical context. Naive character-splitting destroys retrieval quality. | Medium | Python ingest, `split_sections()` + `fixed_chunks()` functions | Neutral |

### Coach Mode (Must Have)

| Feature | Why Expected | Complexity | Dependencies | TFT Policy Note |
|---------|--------------|------------|--------------|-----------------|
| **Line-of-play cards (2-3 options with trade-off)** | "Just tell me what to do" is the #1 user failure mode in game coaching. Providing multiple options with trade-offs empowers decision-making instead of dictating it — and complies with TFT policy. | Medium | Coach prompt template, structured output from LLM | **Critical for TFT compliance** |
| **Trade-off framing (econ, tempo, board cap, pivot fallback)** | TFT decisions are fundamentally about trade-offs. Framing answers around these dimensions gives coach responses professional depth and makes them explainable. | Medium | Coach prompt with explicit trade-off dimensions | Neutral |

### Performance & DevOps (Must Have)

| Feature | Why Expected | Complexity | Dependencies | TFT Policy Note |
|---------|--------------|------------|--------------|-----------------|
| **Healthcheck (app + DB + Ollama)** | Without health checks, debugging startup failures or runtime outages is guesswork. Required for any local-first stack. | Low | `/health` endpoint, checks for Supabase + Ollama connectivity | Neutral |
| **Model keep-alive / warm-up** | Cold model load on RTX 4070 Ti takes 5-15s; pre-loading on app start eliminates the first-request penalty. | Low | Ollama `keep_alive` parameter | Neutral |
| **Query-level caching (short TTL)** | Identical or near-identical TFT queries (patch notes, champion abilities) are common; caching reduces GPU load and improves responsiveness. | Medium | In-memory LRU or file cache for `(query, mode, patch)` keys | Neutral |

---

## Differentiators

Features that set this apart. Not expected out of the box, but valued when present.

### Chat UI Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-----------------|------------|--------------|-------|
| **Inline citation cards (per-sentence or per-paragraph)** | Goes beyond end-of-response citations. Users can hover/tap specific claims to see source snippets. Increases trust dramatically. | High | Citation metadata at chunk/sentence level, UI overlay component | Hard to do well; requires token-level attribution |
| **Streaming citation reveal** | Citations appear alongside streaming tokens, not just at the end. Signals trustworthiness in real-time. | High | Backend citation streaming, frontend partial render | Requires custom SSE event design |
| **Regenerate response** | With same context, regenerate with one click. Useful when first response is off-target. | Low | Backend re-call with same context, frontend button | Simple to add after streaming exists |
| **System prompt / context display** | Users see what context was injected (patch, season, retrieved chunks). Builds transparency. | Low | Display injected context in UI | Neutral UX touch |
| **Keyboard shortcuts** | Power users (TFT players are often gaming-focused) expect Cmd/Ctrl+Enter to send, Escape to abort. | Low | Frontend keyboard listener | Minor but appreciated |

### RAG Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-----------------|------------|--------------|-------|
| **Reranking (cross-encoder post-filter)** | Initial hybrid search returns candidates; reranking improves precision by re-scoring top-K with a cross-encoder or heuristic. Standard 2026 production RAG. | High | Cross-encoder model or heuristic reranker in app layer | MVP should use heuristic rerank (patch/season priority) first |
| **Retrieval debug panel** | Show which chunks were retrieved, their scores, and sources. Helps users understand why an answer was given. Essential for debugging RAG quality. | Medium | `/api/search` debug endpoint, UI panel | Very valuable for iterating on chunking/search |
| **Citation-to-source navigation** | Clicking a citation navigates to the original Obsidian note. Closes the loop between AI answer and personal knowledge. | Medium | Source path metadata in chunks, Obsidian vault path available | Requires consistent vault path linking |
| **Adaptive chunk size by source type** | Obsidian notes vs. patch notes vs. static TFT data may benefit from different chunk sizes. | Medium | Source-type metadata, configurable chunk parameters | Defer to MVP |
| **Embedding cache** | Identical Obsidian chunks don't need re-embedding on re-ingest. Cache by hash reduces compute. | Medium | Hash-based cache check in ingest pipeline | Quick win after MVP |
| **Context compression / summary before injection** | Very long retrieved contexts should be summarized before being added to prompt, preserving context window for the actual answer. | High | Second LLM call for summarization | Defer to post-MVP |

### Coach Mode Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-----------------|------------|--------------|-------|
| **Visual line-of-play cards** | 2-3 options displayed as structured cards with icons (econ, tempo, board cap). Much scannable than prose. | Medium | Structured JSON output from LLM, card component | Key differentiator from generic chat |
| **Pivot fallback chain** | Coach not only recommends a line but shows "if X happens, pivot to Y." Addresses TFT's dynamic nature. | Medium | Multi-step structured output, pivot logic in prompt | Extends Coach prompt |
| **In-game scenario presets** | Pre-built context templates: "fast 8 roll", "hyperoll open", "1-star board holding." Users tap a scenario instead of typing. | Low | Scenario metadata, quick-select UI | Low-effort, high-value |
| **Match context injection** | User pastes board state or uploads screenshot → Coach parses and gives advice. | High | Vision model or text parsing | Defer; complex UX |
| **Coach persona customization** | User selects "aggressive", "safe", "pivoting" coaching style. | Low | System prompt variant, user preference | Simple to add |

### Data Ingestion Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-----------------|------------|--------------|-------|
| **Automated Obsidian sync (n8n scheduled ingest)** | Notes updated in Obsidian should appear in RAG without manual re-ingest. Scheduled 4-hour sync is the MVP approach. | Medium | n8n workflow, `/api/ingest/obsidian` endpoint | Core automation piece from spec |
| **Patch change detection + auto-refresh** | When Riot releases a new patch, the system detects it and re-ingests static data automatically. | Medium | n8n patch check workflow, Riot versions.json polling | Critical for staying current |
| **Data versioning / patch rollback** | If new patch data breaks answers, user can roll back to previous patch version. | Medium | Version snapshots in `documents` table, rollback UI | Important for reliability |
| **Incremental re-ingest (hash-based)** | Only re-embed chunks from files that actually changed. Full re-ingest on every sync wastes compute. | Medium | `source_hash` tracking, conditional re-embed | Already in spec's ingest script |
| **Obsidian file watcher (reactive sync)** | Real-time ingest when a note is saved, not just scheduled. | High | File system watcher (inotify/FSEvents), debouncing | Nice-to-have over scheduled |
| **CommunityDragon fast-path data** | CommunityDragon updates faster than Riot Data Dragon after patches. Use it as a staging source. | Low | CDragon URL integration in ingest script | Already in spec |
| **Localization support (vi_vn)** | Vietnamese-localized TFT data and UI. | Low | Vietnamese locale in static data schema | Core to the app's purpose |

### Session & History Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-----------------|------------|--------------|-------|
| **Session naming / auto-title** | Sessions should be named by content, not just "Session #42". Auto-titling from first user message or summary is expected. | Low | LLM-generated title or heuristics | Simple to add |
| **Session search** | Find past sessions by keyword. | Medium | FTS on session titles/messages, search UI | Leverages existing FTS infrastructure |
| **Session export (JSON/Markdown)** | Export a coaching session as a Markdown note to save in Obsidian. | Low | Export endpoint, file download | Closes the loop with Obsidian |
| **Cross-session memory (long-term)** | App "remembers" your preferences and past mistakes across sessions, not just within one conversation. | High | Persistent user profile, retrieval from past sessions | Significant complexity; consider for v2 |
| **Multiple simultaneous sessions** | Keep Coach and RAG sessions open in parallel tabs. | Low | Frontend multi-tab state, session ID routing | Simple if sessions are ID-based |

### Performance Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-----------------|------------|--------------|-------|
| **Query embedding cache** | Identical queries don't re-embed. 30-minute TTL. | Low | Cache layer keyed by normalized query | Quick win |
| **Static TFT data on-disk cache** | Normalized TFT JSON cached to disk; re-ingest reads cache if patch unchanged. | Low | File cache with patch version check | Already mentioned in spec |
| **Model switching (gemma3:12b for Coach)** | Upgrade to a larger model for Coach mode while keeping qwen3:8b for Normal/RAG. Saves VRAM. | Medium | Model config per mode, Ollama model management | Already in spec's upgrade plan |
| **GPU memory monitoring** | Show current VRAM usage. Warn if model won't fit. | Low | Ollama `/api/ps` endpoint, frontend display | Useful for hardware transparency |

### Dev/Test Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-----------------|------------|--------------|-------|
| **Smoke test suite (20-question eval set)** | Automated check that core RAG + Coach responses don't regress after changes. Industry standard for RAG systems. | Medium | Predefined question set, expected answer criteria, scoring script | Critical for production quality |
| **Retrieval quality metrics (recall@K)** | Measure what percentage of relevant chunks appear in top-K results. Quantifies RAG quality. | Medium | Ground-truth dataset, evaluation script | Important for iteration |
| **Patch date awareness** | System tracks when each data version was ingested and can answer "what was the meta in patch 17.1?" | Low | Timestamp metadata on documents, temporal filtering | Good UX and technical depth |
| **Logging + observability** | Structured logs for every request: query, mode, retrieval results, latency, token usage. | Medium | Python logging, structured JSON logs | Required for debugging |

---

## Anti-Features

### Do NOT Build — TFT Policy Violations

These features explicitly violate Riot Games' TFT policy and must never be implemented, even if users ask for them.

| Anti-Feature | TFT Policy Reason | What to Build Instead |
|--------------|-------------------|----------------------|
| **Real-time opponent scouting / board scanning** | Automatically gathering data on opponents' boards, traits, items, or comps in real-time gives unfair strategic advantage. This is the clearest policy violation. | Static meta analysis, general line-of-play coaching |
| **In-game overlay that dictates decisions** | Any UI element that tells the player "you must roll now", "sell X unit", or "pivot to Y comp" during a match violates the "dictate player decisions" prohibition. | Pre-game coaching, post-game analysis |
| **Matchmaking / ranking integration that provides live counter-picks** | Providing live counter-comps based on current rank or matchmaking is dynamic advantage provision. | Historical matchup analysis from user's own past games |
| **Real-time LP / rank tracking overlay** | Any overlay showing live LP gains/losses or suggesting decisions based on current standing is dynamic real-time data. | Pre-session goal setting, end-of-session review |
| **External data collection or cloud sync of player data** | Sending any player data (match history, board states, decisions) to external servers violates the "local-only" spirit and likely Riot's data policies. | All data stays in Supabase local |
| **Automated "best action" button or macro** | Any feature that automates or pre-fills in-game decisions removes player agency and is explicitly against policy. | Coaching suggestions with human decision-making preserved |
| **Dictating augments or item builds in real-time** | Telling a player "pick Prismatic Ticket" or "build Gunblade" during a live match is dictating decisions. | Pre-match augment strategy discussion, general itemization principles |

### Do NOT Build — Technical / Product Mistakes

These are anti-patterns that cause engineering waste, trust issues, or scope creep.

| Anti-Feature | Why to Avoid | What to Do Instead |
|--------------|--------------|--------------------|
| **Auth/user management for MVP** | Single-user local app; auth adds complexity with zero benefit. | No auth until multi-user need arises |
| **Mobile/non-Windows targets** | Explicitly out of scope for MVP. Different platform means different Ollama GPU support, different Supabase CLI, different UX. | Windows-only for MVP |
| **Complex semantic chunking parser** | Over-engineering chunking before knowing retrieval quality is premature optimization. Heading + fixed-size is sufficient for personal notes. | Simple heading + fixed-size, iterate based on eval results |
| **Redis or distributed cache** | Local app doesn't need distributed caching. Adds operational complexity. | In-memory LRU or file cache is sufficient |
| **Cross-encoder reranking for MVP** | Cross-encoder adds a second model call and complexity. Heuristic reranking (patch priority, season priority) is good enough to start. | Heuristic rerank first; cross-encoder after eval |
| **Full-text search UI (separate from chat)** | Users find answers through chat, not through a search bar. | Keep search inside chat/RAG mode |
| **Multi-file document upload** | Obsidian is the document source. No need for ad-hoc PDF/CSV uploads in MVP. | Obsidian-only ingestion |
| **Real-time WebSocket updates** | SSE is sufficient for streaming. WebSockets add complexity for no benefit in a single-user local app. | SSE streaming only |
| **Containerized Ollama** | Ollama on Windows runs better native (GPU passthrough friction in Docker). Explicitly not recommended in the spec. | Ollama native, API at localhost:11434 |

---

## Dependencies

How features depend on each other. This informs build order.

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Core Chat (Table Stakes - Minimum Viable Product)  │
│                                                             │
│ Streaming responses (SSE)                                   │
│   └─> Mode switching (Normal/RAG/Coach)                    │
│   └─> Abort generation                                     │
│   └─> Chat history list                                     │
│   └─> Message persistence                                   │
│                                                             │
│ Healthcheck                                                 │
│   └─> Model keep-alive / warm-up                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: RAG Foundation (Retrieval + Ingestion)            │
│                                                             │
│ Obsidian vault ingest                                       │
│   └─> Chunking (heading + fixed-size overlap)               │
│   └─> Batch embedding via Ollama                            │
│   └─> Incremental re-ingest (hash-based)                    │
│                                                             │
│ Hybrid search (vector + FTS + RRF)                          │
│   └─> Metadata filtering (patch, season)                    │
│   └─> Basic citation display (end-of-response)             │
│                                                             │
│ TFT static data ingestion                                   │
│   └─> Static data on-disk cache                            │
│   └─> Patch-aware retrieval                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Coach Mode (Differentiation Core)                  │
│                                                             │
│ Coach prompt template                                        │
│   └─> Line-of-play cards (2-3 options)                      │
│   └─> Trade-off framing (econ, tempo, board cap, pivot)     │
│   └─> Pivot fallback chain                                  │
│   └─> In-game scenario presets                              │
│                                                             │
│ Coach model upgrade (gemma3:12b)                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Automation + Performance                          │
│                                                             │
│ n8n scheduled Obsidian ingest                               │
│   └─> Automated patch change detection                      │
│   └─> CommunityDragon fast-path data                        │
│   └─> Data versioning / patch rollback                      │
│                                                             │
│ Query embedding cache                                       │
│   └─> Retrieval debug panel                                 │
│   └─> GPU memory monitoring                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Polish + Eval (Production Quality)                │
│                                                             │
│ Smoke test suite (20-question eval set)                     │
│   └─> Retrieval quality metrics (recall@K)                   │
│   └─> Logging + observability                               │
│                                                             │
│ Session naming / auto-title                                 │
│   └─> Session search                                        │
│   └─> Session export (Markdown to Obsidian)                 │
│                                                             │
│ Inline citation cards                                       │
│   └─> Citation-to-source navigation                         │
│   └─> Streaming citation reveal                             │
│                                                             │
│ Cross-session memory                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Critical Dependency Notes

1. **Streaming must come before everything else** — all other features (abort, citations, coach cards) depend on having a streaming infrastructure.

2. **RAG depends on streaming** — RAG mode needs the streaming chat infrastructure to deliver retrieved contexts.

3. **Coach depends on RAG** — Coach mode retrieves TFT static data and personal notes; it builds on the RAG retrieval layer.

4. **Citation display depends on retrieval metadata** — citation quality depends on chunk metadata (source path, heading, patch) being populated during ingest.

5. **Automation depends on ingest APIs** — n8n workflows call the ingest endpoints; those endpoints must exist first.

6. **Eval depends on core features** — smoke tests only make sense once the app does something worth testing.

---

## MVP Recommendation

### Priority Build Order

**Must ship in MVP (Table Stakes):**
1. Streaming responses + abort
2. Mode switching (Normal / RAG / Coach)
3. Chat history + message persistence
4. Basic citation display (end-of-response)
5. Obsidian ingest (file-based, on-demand)
6. Hybrid search (HNSW + FTS + RRF)
7. Metadata filtering (patch, season)
8. TFT static data ingestion (champions, traits, items, augments)
9. Coach prompt template with line-of-play framing
10. Healthcheck + model keep-alive

**Ship in v2 (Differentiators with moderate complexity):**
1. Retrieval debug panel
2. Session auto-naming
3. Query embedding cache
4. n8n scheduled Obsidian sync
5. Patch change detection + auto-refresh
6. In-game scenario presets
7. Coach pivot fallback chain
8. Citation-to-source navigation

**Ship in v3 (Differentiators with high complexity):**
1. Inline citation cards (per-sentence)
2. Streaming citation reveal
3. Cross-encoder reranking
4. Cross-session memory
5. Smoke test suite + retrieval metrics

### Do NOT Build (Ever, for MVP or Beyond):
- Real-time opponent scouting
- In-game overlay or decision dictation
- Automated "best action" features
- Cloud APIs or external data collection
- Auth/user management
- Non-Windows targets

---

## Sources

| Source | Confidence | Used For |
|--------|------------|----------|
| deep-research-report.md | HIGH | Architecture, stack, schema, prompts, automation, TFT policy context |
| Graphlit Developer Guides — "Building AI Chat Applications" | HIGH | Streaming, citations, RAG core patterns |
| Dasroot.net — "Streaming RAG Responses with Token-Level Citations" | MEDIUM | Token-level citation patterns |
| Neuramonks — "Standard RAG Is Dead — Here's What's Replacing It in 2026" | MEDIUM | Modern RAG patterns, hybrid retrieval, reranking |
| Medium — "Java RAG in 2026 — The Only Guide You'll Ever Need" | MEDIUM | RAG production patterns, observability, idempotency |
| Medium — "Modern RAG in 2026: The Components That Actually Matter" | MEDIUM | Citations, freshness, entity-filtered RAG |
| Reddit — "I built a TFT coach that analyzes your actual match history" | MEDIUM | TFT coaching feature expectations |
| DataTFT — "AI Guide Features" | MEDIUM | AI Quick Query, text-based coaching |
| Riot Games — TFT API policy | HIGH | TFT policy compliance requirements |
| Xeynergy Blog — "How I Built a RAG AI Assistant That Actually Remembers" | MEDIUM | Session persistence, conversational memory |
| Blitz.GG Press — ML for TFT composition analysis | LOW | Competitive TFT tooling context |
