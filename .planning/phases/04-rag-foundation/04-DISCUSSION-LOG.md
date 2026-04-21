# Phase 4: RAG Foundation - Discussion Log (Assumptions Mode)

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the analysis.

**Date:** 2026-04-22
**Phase:** 04-rag-foundation
**Mode:** assumptions (auto)
**Areas analyzed:** Retrieval Integration, Citation Events, Obsidian Ingest, Prompt Injection, Search Endpoint, Schema Alignment

## Assumptions Presented

### Retrieval Integration
| Assumption | Confidence | Evidence |
|-----------|------------|----------|
| Modify `build_messages()` to prepend context for rag/coach modes | Confident | `apps/backend/app/routes/chat.py` — `build_messages()` already exists, mode parameter available |
| Use `hybrid_search_chunks` from 0001 migration (0.7/0.3 weights) | Confident | `supabase/migrations/0001_initial_schema.sql` — function exists, returns id/content/source/metadata/similarity |
| Call retrieval before streaming, inject once | Confident | PITFALLS.md — "do NOT stream citations mid-generation" pattern |
| Ignore 0002 migration function (references wrong table) | Confident | `0002_create_function.sql` — queries `document_chunks` table which doesn't exist |

### Citation Events
| Assumption | Confidence | Evidence |
|-----------|------------|----------|
| Emit `event: citation` before first token event | Confident | ARCHITECTURE.md — "Context Assembly + Prompt" happens before "Ollama /api/chat" |
| Frontend `onCitation` handler already wired | Confident | `apps/frontend/src/hooks/useStreamingMessages.ts` — `onCitation` callback appends to citations array |
| Citation format: {id, source, heading, text, score} | Confident | `apps/frontend/src/api/types.ts` — `Citation` interface already defines these fields |

### Obsidian Ingest
| Assumption | Confidence | Evidence |
|-----------|------------|----------|
| Update `rag_chunk_size` default to 2000 chars | Confident | ARCHITECTURE.md — "2000 chars" recommendation, config.py has `rag_chunk_size: int = 512` |
| Add 500-char overlap to `split_into_chunks()` | Confident | ARCHITECTURE.md — "25% overlap" recommendation |
| Batch embedding: 16 chunks per request | Confident | STATE.md — "VRAM budget: 16GB, batch embedding capped at 16 chunks" |
| Add `generate_embeddings()` to `ollama.py` for batch API | Confident | `app/services/ollama.py` — has single `generate_embedding()`, needs batch equivalent |

### Prompt Injection
| Assumption | Confidence | Evidence |
|-----------|------------|----------|
| Context block as special `user` message with `---CONTEXT---` delimiters | Likely | `prompts.py` — rag prompt already instructs `[source]` markers, model self-cites |
| Coach uses same retrieval as RAG | Confident | ARCHITECTURE.md — "RAG/Coach" in same data flow branch |
| Do NOT add game state — user provides in message | Confident | `prompts.py` coach prompt — "Based on their board..." expects user input |

### Search Endpoint
| Assumption | Confidence | Evidence |
|-----------|------------|----------|
| Create `app/routes/search.py` with POST /api/search | Likely | `models.py` — `SearchRequest` model already exists, unused |

### Schema Alignment
| Assumption | Confidence | Evidence |
|-----------|------------|----------|
| Store heading path in `metadata` JSONB, not new column | Confident | `chunks` table has `metadata JSONB`, no migration needed |
| Do NOT alter `chunks` table schema | Confident | Minimal approach — avoid schema changes for MVP |

## Corrections Made

No corrections — all assumptions auto-confirmed in `--auto` mode.

## Auto-Resolved

- Retrieval: Confident — no user correction needed
- Citation: Confident — frontend already wired
- Ingest: Confident — codebase patterns confirm approach
- Prompt injection: Likely — auto-resolved with recommended defaults
- Search endpoint: Likely — auto-resolved with recommended defaults
- Schema: Confident — minimal change approach confirmed

## External Research

No external research needed — codebase provides sufficient evidence for all assumptions.

