# ROADMAP: TFT Local Copilot v1.4

**Project:** TFT Local Copilot
**Version:** v1.4 "Smart & Polished"
**Created:** 2026-04-23
**Granularity:** standard
**Parallelization:** enabled

---

## Milestone Summary

| Milestone | Phases | Status | Ship Date |
|-----------|--------|--------|-----------|
| ✅ v1.0 MVP | 1–7 | SHIPPED 2026-04-22 | 60/60 smoke test |
| ✅ v1.1 TFT Meta Mastery | 8 | SHIPPED 2026-04-22 | PATCH-01..05 |
| ✅ v1.2 MetaTFT Intelligence | 9 | SHIPPED 2026-04-23 | META-01..05 |
| ✅ v1.3 Hardening & Polish | 10 | SHIPPED 2026-04-23 | HARD-01..05 + 2 root fixes |
| 🔄 **v1.4 Smart & Polished** | **11–14** | **IN PROGRESS** | **TBD** |

---

## Phases

---

### Phase 11: TFT Knowledge Graph

**Goal:** Build an in-memory knowledge graph from Set 17 data (champions, items, traits, augments, systems) that enables cross-entity traversals and structured queries. This is the foundation that makes "smart" answers possible — not just retrieval, but reasoned connections.

**Why:** Currently the system answers questions about champion-item synergies, trait breakpoints, or augment interactions using raw text search. A knowledge graph lets the LLM traverse relationships: "Soraka items?" → Soraka node → item edges. "Which 3-cost carries work with Anima?" → trait node → champion edges → item edges.

**Scope:**
- Define node types: Champion, Item, Trait, Augment, God, System
- Define edge types: `HAS_TRAIT`, `BUILDS_FROM`, `SYNERGIZES_WITH`, `COUNTERS`, `COUNTERED_BY`, `COUNTERS_TRAIT`
- Load data from verified JSON packs into NetworkX (in-memory, fast, Python-native)
- Expose `GET /api/graph/query` for structured graph traversals
- Expose `GET /api/graph/neighbors/{entity}` for direct neighbor lookups
- Expose `POST /api/graph/ingest` to reload/reload the graph from JSON files
- Auto-reload graph when new patch data is ingested (emit event from ingest pipeline)

**Knowledge Graph Entity Types:**
```
Champion: {name, cost, traits[], ability_summary, items_ideal[], role}
Item: {name, category, stats[], builds_from[], component_of[], effect_text}
Trait: {name, type, breakpoints{}, champions[], description}
Augment: {name, tier, description, relevant_champions[]}
God: {name, title, focus, reward_tiers{}}
System: {name, description, mechanics[]}
```

**Knowledge Graph Edge Types:**
```
HAS_TRAIT(champion, trait, count)       # Briar → Anima (1)
BUILDS_FROM(item, component_a, component_b)  # Giant Slayer: B.F.Sword + RecurveBow
ITEM_FOR_CHAMPION(item, champion)        # Bloodthirster → Briar
TRAIT_BREAKPOINT(trait, count, bonus)   # Anima → 3 → "Start Researching!"
SYNERGIZES(champion, champion)           # Dark Star pairs
COUNTERS(champion, champion)             # matchup data from meta
GOD_ALIGNMENT(god, trait)               # Soraka → Anima (HP focus)
```

**Plans:**
- [x] `11-01-PLAN.md` — Knowledge Graph schema + NetworkX data model
- [x] `11-02-PLAN.md` — `/api/graph/query` + `/api/graph/neighbors/{entity}` endpoints
- [x] `11-03-PLAN.md` — Auto-reload on patch ingest + hot-reload endpoint
- [x] `11-04-PLAN.md` — Unit tests for graph traversals (edge cases, missing nodes)

**Depends on:** Phase 5 (TFT Static Data already ingested), Phase 8 (patch monitoring)

**Traceability:** KNOW-01 through KNOW-04

---

### Phase 12: UI/UX Core Redesign

**Goal:** Fix the layout overflow bugs and create a polished, responsive chat interface. Fix the message overflow issue where long messages stretch the container and break component alignment. Create a modern, TFT-themed UI that renders rich content gracefully.

**Why:** The UI screenshot shows messages that "dò ra" (stretch out) horizontally. Root causes:
1. `MessageList.tsx` message container has no `max-width` enforcement on the parent flex column
2. `MessageList` container uses `flex-1` without `min-w-0` — flex items can overflow
3. `ChatShell` sidebar + main area layout has no overflow protection
4. Citation cards and CompCards use inline styles, not Tailwind — hard to maintain
5. No responsive breakpoints for mobile/tablet
6. Long URLs and code blocks overflow instead of wrapping

**Problems to fix:**
1. **Message overflow** — Long assistant messages stretch the message bubble container, causing sidebar and other components to shift. Fix: `max-w-[70%]` on message bubble, but parent container needs `min-w-0` and `overflow-x-hidden`
2. **MessageList scroll** — Container needs `overflow-y-auto` and proper height constraints
3. **CitationCard** — `line-clamp-3` cuts off important info; needs expand-on-click
4. **CompCard** — Inline styles mixed with Tailwind; needs Tailwind migration + proper type safety
5. **Header layout** — `w-64` on ModeTabs is fragile; use flex/gap instead
6. **Composer** — Long text should wrap; send button should stay visible
7. **Empty state** — Improve the welcome screen with TFT theming

**Plans:**
- [x] `12-01-PLAN.md` — Layout refactor: fix overflow, `min-w-0`, `max-w-[70%]` enforcement, scroll isolation
- [x] `12-02-PLAN.md` — CitationCard v2: expandable on click, collapsible sections, source filtering
- [x] `12-03-PLAN.md` — CompCard Tailwind migration: replace inline styles with Tailwind classes, add type safety
- [x] `12-04-PLAN.md` — Responsive breakpoints: mobile sidebar collapse, tablet layout, touch targets
- [x] `12-05-PLAN.md` — Loading states + streaming UX polish: typing indicator improvement, progressive message reveal

**Status:** ✅ Complete (2026-04-23)

**Depends on:** None (independent of backend)

**Traceability:** UI-01 through UI-05

---

### Phase 13: Smart Chat Engine

**Goal:** Upgrade the chat system to deliver intelligent, cross-entity answers that leverage the knowledge graph. Instead of returning raw text chunks, the system should understand entity types and render structured cards (ChampionProfile, ItemCard, TraitCard, AugmentCard) inline in chat responses. Also add smart reply suggestions and contextual help.

**Why:** The user said "I want answers to be smarter, not just standalone text lines." The current system returns markdown text. We need structured entity rendering with cross-references.

**Smart Reply Suggestions:**
- After user sends a message, show 2-3 contextually relevant suggestions
- Suggestions come from knowledge graph: "Try [champion] with [items]", "See [trait] breakdown", "Best augments for [context]"
- Dismissable chip buttons above the Composer

**Contextual Entity Rendering (inline in chat):**
The LLM produces structured JSON markers in the response that the frontend parses and renders as rich cards:

```json
{"type": "champion", "name": "Briar", "cost": 3, "traits": ["Anima 1"], "ability": "Chaos Frenzy"}
{"type": "item", "name": "Bloodthirster", "category": "AD", "stats": ["+15% AD", "+15% AP"]}
{"type": "trait", "name": "Anima", "count": 3, "bonus": "Start Researching!"}
{"type": "augment", "name": "AFK", "tier": "Silver", "effect": "No actions for 3 rounds, then +20 gold"}
```

**Smart Routing:**
```
"best items for Briar?"        → Knowledge Graph: Briar node → item edges → ChampionProfile + ItemCards
"what traits work with Soraka?" → Knowledge Graph: Soraka node → trait edges → TraitCards  
"is Anima good this patch?"    → Knowledge Graph + RAG: trait query + patch context → combined answer
"top 3 comps right now?"       → RAG + MetaTFT: top S-tier comps → CompCards (existing)
"rolling odds at level 7?"      → Knowledge Graph: System/Rolling odds → StatTable inline
"compare IE vs GS"             → Knowledge Graph: Item nodes → side-by-side ItemCards
```

**Plans:**
- [ ] `13-01-PLAN.md` — Smart entity JSON markers in LLM prompts + frontend JSON parser → entity cards
- [ ] `13-02-PLAN.md` — ChampionProfile, ItemCard, TraitCard, AugmentCard inline components
- [ ] `13-03-PLAN.md` — Smart reply suggestions (context-aware chips from knowledge graph)
- [ ] `13-04-PLAN.md` — Cross-entity query routing: graph-first, rag-fallback, metaTFT enrichment
- [ ] `13-05-PLAN.md` — Coach mode enhancement: pivot fallback chain + in-game scenario presets

**Depends on:** Phase 11 (Knowledge Graph), Phase 12 (UI/UX foundation)

**Traceability:** SMART-01 through SMART-05

---

### Phase 14: RAG 2.0 + Full Data Ingest

**Goal:** Enhance the retrieval pipeline with metadata filtering by entity type, streaming citations, heuristic reranking by patch/season priority, and ingest all Set 17 verified data into the vector DB. Replace the flat 32-chunk ingest with a rich, structured corpus of 252 augments + 59 champions + 45+ items + traits + systems + rolling odds.

**Why:** The current RAG pipeline has 32 chunks. User has verified data files with:
- 252 augments (Silver/Gold/Prismatic)
- 59 champions (Set 17)
- 45+ items (components, standard, radiant, emblem, artifact)
- 30+ traits with breakpoints
- 9 Space Gods systems
- Rolling odds by level

**Metadata Filtering Enhancement:**
Current: `hybrid_search_chunks_by_patch(query, text, top_k, patch)`
Enhanced: `hybrid_search_chunks($1, $2, $3, $4, $5)` where `$5` is entity_type filter:
- `champion` → filter `metadata->>'type' = 'champion'`
- `item` → filter `metadata->>'type' = 'item'`
- `trait` → filter `metadata->>'type' = 'trait'`
- `augment` → filter `metadata->>'type' = 'augment'`
- `system` → filter `metadata->>'type' = 'system'`

**Heuristic Reranking:**
Current rank = cosine similarity
Enhanced rank = cosine_similarity × patch_priority × entity_priority × recency_boost

Where:
- `patch_priority`: current patch (17.1) = 1.0, previous patch (16.8.1) = 0.7, older = 0.3
- `entity_priority`: `champion` > `item` > `trait` > `augment` > `system` for meta questions
- `recency_boost`: 1.2x for chunks ingested in last 7 days

**Streaming Citations:**
Currently citations appear after the full response. Streaming mode:
1. `{"type": "citation_start", "data": {"id": "c1", "source": "metatft"}}` — opens a "streaming source" indicator
2. Tokens stream into the response
3. `{"type": "citation_end", "data": {"id": "c1", "text": "...", "score": 0.87}}` — finalizes the citation

**Full Ingest Sources:**
```
augments_full_user_verified.json     → 252 augments × 200-500 chars → ~200 chunks
traits_full_user_verified.json        → 30+ traits × 300 chars → ~60 chunks  
items_effects_expanded_set17.json     → 45+ items × 300 chars → ~80 chunks
tft_set17_patch17_1_deep_pack.json   → champions + systems × 400 chars → ~120 chunks
rolling_odds_user_verified.json       → rolling odds table × 200 chars → ~20 chunks
tft_set17_patch17_1_enhanced_pack.json → Space Gods system details × 300 chars → ~40 chunks
```
**Total target:** 500+ high-quality chunks with entity-type metadata

**Plans:**
- [ ] `14-01-PLAN.md` — Metadata filtering: add entity_type column + enhanced hybrid_search function
- [ ] `14-02-PLAN.md` — Heuristic reranking: patch/season/entity priority boost before RRF
- [ ] `14-03-PLAN.md` — Streaming citations: SSE events for citation_start/citation_end
- [ ] `14-04-PLAN.md` — Full ingest pipeline: 252 augments + 59 champions + items + traits + systems
- [ ] `14-05-PLAN.md` — Obsidian file watcher for real-time reactive sync (RAG-12 from v2 deferred)

**Depends on:** Phase 4 (RAG Foundation), Phase 5 (TFT Static Data)

**Traceability:** RAG2-01 through RAG2-05

---

## Progress Table

| Phase | Milestone | Plans | Status | REQ-IDs |
|-------|-----------|-------|--------|---------|
| 11 | v1.4 | 4/4 | ✅ Complete (2026-04-23) | KNOW-01..04 |
| 12 | v1.4 | 5/5 | ✅ Complete (2026-04-23) | UI-01..05 |
| 13 | v1.4 | 5/5 | 📋 Planned | SMART-01..05 |
| 14 | v1.4 | 5/5 | 📋 Planned | RAG2-01..05 |

---

## Requirements Index

| REQ-ID | Description | Phase |
|--------|-------------|-------|
| KNOW-01 | NetworkX knowledge graph with Champion/Item/Trait/Augment/God/System nodes | 11 |
| KNOW-02 | `/api/graph/query` + `/api/graph/neighbors/{entity}` endpoints | 11 |
| KNOW-03 | Auto-reload graph on patch ingest + hot-reload API | 11 |
| KNOW-04 | Unit tests for graph traversals (missing nodes, edge cases) | 11 |
| UI-01 | Layout refactor: overflow fix, min-w-0, max-w enforcement | 12 |
| UI-02 | CitationCard v2: expandable, collapsible, source filter | 12 |
| UI-03 | CompCard Tailwind migration + type safety | 12 |
| UI-04 | Responsive breakpoints: mobile sidebar, tablet layout | 12 |
| UI-05 | Loading states + streaming UX polish | 12 |
| SMART-01 | Smart entity JSON markers + frontend parser | 13 |
| SMART-02 | ChampionProfile/ItemCard/TraitCard/AugmentCard components | 13 |
| SMART-03 | Smart reply suggestions (context-aware chips) | 13 |
| SMART-04 | Cross-entity query routing: graph-first, rag-fallback | 13 |
| SMART-05 | Coach mode enhancement: pivot chain + scenario presets | 13 |
| RAG2-01 | Metadata filtering by entity_type in hybrid search | 14 |
| RAG2-02 | Heuristic reranking: patch/entity/recency priority boost | 14 |
| RAG2-03 | Streaming citations: citation_start/citation_end SSE events | 14 |
| RAG2-04 | Full ingest: 252 augments + 59 champions + items + traits + systems | 14 |
| RAG2-05 | Obsidian file watcher for real-time reactive sync | 14 |

---

## TFT Policy Compliance (Unchanged)

All phases continue to comply with Riot TFT policy:
- **No real-time data:** Never build overlay, screen capture, or opponent scouting features
- **No game state reading:** Coach mode suggestions based on user's stated context only
- **Suggest, don't dictate:** Coach responses frame recommendations as options with trade-offs
- **Local-only:** All data stays on user's machine
- **Unofficial tool:** Clearly disclaim no affiliation with Riot Games

---

## Deferred from v2 (Not in v1.4)

These remain in the backlog for future milestones:
- Model upgrade: gemma3:12b for Coach mode (MODEL-01)
- Session export to Obsidian (SESS-03)
- Cross-session memory (SESS-04)
- Retrieval debug panel (RAG-10)
- Eval/observability suite (EVAL-01..03)

---

## Archive

- [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md) — v1.0 MVP
- [.planning/milestones/v1.1-ROADMAP.md](.planning/milestones/v1.1-ROADMAP.md) — v1.1 TFT Meta Mastery
- [.planning/milestones/v1.2-ROADMAP.md](.planning/milestones/v1.2-ROADMAP.md) — v1.2 MetaTFT Intelligence

---

*Created: 2026-04-23*
*v1.4 "Smart & Polished" — Phase 11-14*
