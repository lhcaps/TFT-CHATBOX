# TFT Local Copilot

## What This Is

A local-first AI copilot for Teamfight Tactics (TFT) that runs entirely on the user's machine — no cloud APIs, no external dependencies. It combines a React chat UI with a FastAPI backend powered by Ollama (local LLM), Supabase (Postgres + pgvector for RAG), and Obsidian as a knowledge source. Three modes: **Normal** (free chat), **RAG** (retrieve from notes/patch data), and **Coach** (suggest 2-3 lines of play with trade-off analysis).

## Core Value

A TFT player can ask comp questions, patch notes, augment choices, or pivot strategies — and get grounded, locally-sourced answers without leaving the game ecosystem.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Local LLM chat with streaming responses (Ollama + qwen3:8b)
- [ ] Three mode system: Normal / RAG / Coach
- [ ] RAG retrieval from Obsidian Markdown vault
- [ ] Hybrid search (full-text + semantic via pgvector HNSW)
- [ ] TFT static data ingestion (champions, traits, items, augments)
- [ ] Reactive chat UI (React + Vite + Tailwind)
- [ ] FastAPI backend with session/message persistence
- [ ] Obsidian vault ingest pipeline with chunking + embedding
- [ ] n8n automation for scheduled ingest + patch monitoring
- [ ] ngrok for exposing webhooks when needed

### Out of Scope

- Real-time opponent scouting / overlay — violates Riot TFT policy
- Cloud API dependencies — must remain fully local
- Mobile or non-Windows targets for MVP
- Auth/user management — single local user

## Context

- **Hardware**: 64GB RAM + RTX 4070 Ti SUPER 16GB VRAM
- **Models**: qwen3:8b (chat), qwen3-embedding:4b (embedding), gemma3:12b (optional upgrade)
- **Season**: Set 17 Space Gods, Patch 17.1+
- **Design source**: deep-research-report.md (extensive spec covering architecture, stack, SQL schema, prompts, automation)
- **TFT policy**: No real-time data, scouting, or "dictate player decisions" tools

## Constraints

- **Privacy**: All data stays local — Ollama, Supabase, Obsidian all on-machine
- **Performance**: Must fit in 16GB VRAM — max 8B chat model, 4B embedding model
- **TFT Policy Compliance**: No dynamic real-time overlay or opponent scouting features
- **Stack stability**: Windows-native Ollama, Supabase local CLI, Docker Compose for app/n8n

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Ollama native (not containerized) | GPU passthrough friction in Docker on Windows | — Pending |
| 1024-dim embeddings | HNSW index limit 2000 dims, Ollama supports flexible dims | — Pending |
| Supabase local CLI | Postgres + pgvector + dashboard without self-managed services | — Pending |
| 3-mode chat (Normal/RAG/Coach) | Complies with TFT policy while being useful | — Pending |
| Obsidian as knowledge source only | Vault is Markdown/text — not a runtime dependency | — Pending |
| n8n for automation | Best for cron ingest + webhook fan-out | — Pending |

---
*Last updated: 2026-04-22 after initialization*
