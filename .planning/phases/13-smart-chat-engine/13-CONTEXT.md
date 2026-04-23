# Phase 13: Smart Chat Engine - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Upgrade the chat system to deliver intelligent, cross-entity answers that leverage the knowledge graph. The LLM produces structured JSON markers in responses that the frontend parses and renders as rich entity cards (ChampionProfile, ItemCard, TraitCard, AugmentCard) inline in chat. Also add smart reply suggestions and enhanced query routing.

**Scope:**
- Smart entity JSON markers in LLM prompts + frontend JSON parser → entity cards
- ChampionProfile, ItemCard, TraitCard, AugmentCard inline components
- Smart reply suggestions (context-aware chips from knowledge graph)
- Cross-entity query routing: graph-first, rag-fallback, metaTFT enrichment
- Coach mode enhancement: pivot fallback chain + in-game scenario presets

**Out of scope:**
- Streaming citations (Phase 14 RAG2-03)
- Obsidian file watcher (Phase 14 RAG2-05)
- Metadata entity type filtering in RAG (Phase 14 RAG2-01)
- Model upgrade (MODEL-01)

</domain>

<decisions>
## Implementation Decisions

### JSON Parser (D-01)
- **Streaming incremental parse:** Parse entity JSON markers incrementally as they appear in the SSE token stream — render cards progressively as markers complete
- **Malformed JSON fallback:** Render invalid JSON as a code block (preserve visibility, let user see what went wrong)
- **Buffering strategy:** Buffer JSON fragments until complete `{...}` object detected, then parse immediately
- **Incremental rendering:** Render entity cards as soon as their JSON is complete, before the full response finishes

### Card Design System (D-02)
- **Theme:** Cosmic accents on minimal layout — cosmic color palette (purple/blue hues) and themed icons/colors, but clean minimal card structure (not full cosmic gradient backgrounds). **"Đủ để biết là mùa gì nhưng vẫn ấn tượng"**
- **ChampionProfile:**
  - Cost: tier-colored text (1=gray-400, 2=green-400, 3=blue-400, 4=purple-400, 5=yellow-400) — NO badge icons
  - Trait badges: small colored pills
  - Compact horizontal layout: `[Name] | [Trait] [Trait] | Ability: X`
- **ItemCard:**
  - Category: color-coded badge (AD=red, AP=blue, Tank=green, Support=purple) — NO emoji icons
  - Recipe shown as component names
  - Stats + effect text
- **TraitCard:**
  - Type badge (Origin/Class)
  - Tier count highlighted
  - Champion list as small badges
  - Active breakpoint highlighted
- **AugmentCard:**
  - Tier badge (Silver/Gold/Prismatic with color)
  - Effect text
  - Related champions if applicable
- **All cards:** Dark theme matching `gray-900` background, subtle borders, hover lift effect

### Suggestion Chips (D-03)
- **Position:** Sticky above Composer — always visible, does not scroll away
- **Count:** 2-3 chips per suggestion set
- **Behavior:** Click to auto-fill and send; dismissible with X button
- **Animation:** Fade-in on appearance (200ms)
- **API:** `GET /api/graph/suggest?context={message}&limit=3` — uses knowledge graph to generate
- **Fallback:** Hardcoded static suggestions if API fails

### Query Router (D-04)
- **Approach:** Graph-first, RAG fallback, MetaTFT enrichment
- **Pattern:** Knowledge Graph for direct entity lookups (champion stats, trait breakpoints, item recipe); RAG for complex questions (patch notes, strategy); MetaTFT for meta/comp queries
- **Result merging:** Merge all results from multiple sources with source attribution and deduplication
- **Routing examples:**
  - `"best items for Briar?"` → Graph (Briar → items) → RAG fallback
  - `"is Anima good?"` → Graph + RAG (patch context)
  - `"top comps?"` → RAG (MetaTFT chunks)
  - `"rolling odds at level 7?"` → Graph (SystemNode: rolling_odds)
  - `"compare IE vs GS"` → Graph (ItemNode) → RAG
- **Implementation:** FastAPI dependency class `QueryRouter` — classify query type, call sources in parallel/sequence, merge results

### Coach Mode Enhancement (D-05)
- **Visual format:** Line-of-play cards — visual box/card layout for each line of play (primary + pivot fallback)
- **Pivot fallback:** Always included after 2-3 lines of play
- **Scenario presets:** Both approaches — tag prefix in message + separate mode/preset option in UI
  - `[fast8]` — Fast 8 roll
  - `[hyperoll]` — Hyperoll
  - `[1star]` — 1-star holding
  - `[lategame]` — Stage 5+
- **Preset UI:** Subtle dropdown or chip group in the header/Composer area (not a full mode change)

### LLM Prompt Strategy (D-06)
- **RAG mode prompt:** Add entity JSON marker instruction to system prompt
- **Coach mode prompt:** Add pivot fallback + scenario tag recognition to system prompt
- **No new LLM model:** Continue using qwen3:1.7b (current model)

### the agent's Discretion
- Exact CSS values for cosmic accent colors (may refine during implementation)
- Exact component file structure (single file per card vs shared base)
- Whether to use `dangerouslySetInnerHTML` or React parsing for markdown text in cards
- Suggestion chip max-width and truncation strategy
- Router confidence threshold for merging secondary sources

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/ROADMAP.md` — Phase 13 goal, scope, SMART-01..05, traceability, Depends on: Phase 11, Phase 12
- `.planning/REQUIREMENTS.md` — SMART-01..05 acceptance criteria
- `.planning/STATE.md` — current project state, Phase 11 complete, Phase 12 complete
- `.planning/PROJECT.md` — project vision, stack summary, locked decisions: entity JSON markers, graph-first routing

### Prior Phase Context
- `.planning/phases/11-tft-knowledge-graph/11-CONTEXT.md` — graph endpoints, lazy-load strategy, node types, edge types
- `.planning/phases/12-ui-ux-redesign/12-CONTEXT.md` — UI decisions, cosmic theme colors, component patterns

### Backend Codebase
- `apps/backend/app/routes/chat.py` — chat endpoint, `build_messages()`, `stream_ollama_tokens()`, SSE event format
- `apps/backend/app/prompts.py` — existing system prompts for normal/rag/coach modes
- `apps/backend/app/routes/graph.py` — existing graph endpoints: `/query`, `/neighbors/{entity}`, `/reload`, `/ingest`
- `apps/backend/app/graph/models.py` — Pydantic models for graph responses
- `apps/backend/app/services/retrieval.py` — existing `retrieve_chunks()` function
- `apps/backend/app/config.py` — settings management

### Frontend Codebase
- `apps/frontend/src/components/MessageList.tsx` — message rendering, citation source filter, streaming dots (line 118-138: MessageContent component)
- `apps/frontend/src/components/CompCard.tsx` — existing card component (295→180 lines, cosmic theme, tier colors)
- `apps/frontend/src/utils/compParser.ts` — `parseCompBlocks()` and `parseCompCard()` — reference for parsing patterns
- `apps/frontend/src/api/types.ts` — Message, Citation, SSEEvent types
- `apps/frontend/src/components/Composer.tsx` — input component (where suggestions will be placed above)

### Data Files
- `tft_set17_patch17_1_deep_pack_v4_user_verified.json` — champion cost, traits, ability for ChampionProfile
- `items_effects_expanded_set17.json` — item category, stats, effect for ItemCard
- `traits_full_user_verified.json` — trait breakpoints, champions for TraitCard

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MessageList.tsx` `MessageContent` component: renders markdown paragraphs + CompCard — this is where entity cards will be integrated
- `CompCard.tsx`: existing card component with cosmic theme, tier colors, glow effects — reference for card structure
- `parseCompBlocks()`: regex-based block parser — entity JSON parser can use similar pattern
- `SSEEvent` type in `types.ts`: `token | done | usage | citation | error` — new entity card events can use `entity_card` type
- `stream_ollama_tokens()`: token streaming — entity markers come through as text tokens, need regex extraction

### Established Patterns
- Cosmic theme: purple-400/500, blue-400/500, glow effects via shadow
- Dark theme: `bg-gray-900`, `text-white`, `border-gray-700`
- Tier colors: S=yellow-400, A=gray-300, B=orange-400
- Card hover: `hover:shadow-lg hover:-translate-y-0.5 transition-all`
- Streaming dots: purple-400 animated bounce (already in MessageList)

### Integration Points
- `MessageList.tsx` line 45: `<MessageContent content={msg.content} />` — JSON parser goes here
- `Composer.tsx`: suggestion chips go above the textarea
- `apps/backend/app/routes/chat.py`: query router calls graph + retrieval services
- `apps/backend/app/prompts.py`: entity marker instructions added to RAG/Coach prompts
- `apps/frontend/src/api/types.ts`: add `EntityCard` type, `Suggestion` type

</code_context>

<specifics>
## Specific Ideas

### Entity JSON Marker Format (from ROADMAP)
```json
{"type": "champion", "name": "Briar", "cost": 3, "traits": [{"name": "Anima", "count": 1}], "ability": "Chaos Frenzy", "role": "carry"}
{"type": "item", "name": "Bloodthirster", "category": "AD", "stats": ["+15% AD", "+15% AP"], "effect": "..."}
{"type": "trait", "name": "Anima", "count": 3, "bonus": "Start Researching!"}
{"type": "augment", "name": "AFK", "tier": "Silver", "effect": "..."}
```

### Card Component Structure
```tsx
// ChampionProfile — minimal cosmic accent
<div className="border border-purple-500/30 rounded-lg p-3 bg-gray-800/50">
  <span className="text-blue-400 font-bold">Briar</span>
  <span className="text-purple-400 text-sm ml-2">3-cost</span>
  <div className="flex gap-1 mt-1">
    <span className="text-xs px-2 py-0.5 rounded bg-purple-900/50 text-purple-300">Anima 1</span>
  </div>
</div>
```

### Line-of-Play Card (Coach Mode)
```
╔══════════════════════════════════════╗
║ 🎯 PRIMARY: Dark Star 6             ║
║ Econ: 30g after krugs → roll at 4-2║
║ Pivot: 4 Anima if contested          ║
╚══════════════════════════════════════╝
```

### Suggestion Chips
```tsx
<div className="sticky top-0 z-10 bg-gray-900/95 backdrop-blur border-b border-gray-800 px-4 py-2 flex gap-2">
  {suggestions.map((s) => (
    <button className="text-sm px-3 py-1.5 rounded-full bg-purple-900/50 text-purple-300 border border-purple-500/30 hover:bg-purple-800/50">
      {s.text} →
    </button>
  ))}
</div>
```

</specifics>

<deferred>
## Deferred Ideas

### Future Phase Candidates
- **Phase 14 (RAG 2.0)** — Streaming citations (citation_start/citation_end SSE events)
- **Phase 14 (RAG 2.0)** — Obsidian file watcher for real-time reactive sync
- **Phase 14 (RAG 2.0)** — Metadata entity type filtering (champion/item/trait/augment/system filter in hybrid_search)
- **v2 (MODEL-01)** — Model upgrade to qwen3:8b or gemma3:12b for better Coach reasoning
- **v2 (SESS-03)** — Session export as Markdown to Obsidian
- **v2 (EVAL-01..03)** — Eval/observability suite

### Out of Scope for Phase 13
- WebSocket instead of SSE (already locked)
- Cross-session memory
- Retrieval debug panel

</deferred>

---

*Phase: 13-smart-chat-engine*
*Context gathered: 2026-04-23*
