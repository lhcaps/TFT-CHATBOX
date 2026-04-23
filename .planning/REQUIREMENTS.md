# Requirements: TFT Local Copilot v1.4 "Smart & Polished"

**Defined:** 2026-04-23
**Version:** v1.4
**Goal:** Smart interconnected TFT knowledge + polished UI + enhanced RAG + full data ingest

---

## v1.4 Requirements

### Phase 11: Knowledge Graph (KNOW-01..04)

#### KNOW-01: NetworkX Knowledge Graph
**Phase:** 11 | **Plan:** 11-01

Define and build an in-memory directed multigraph using NetworkX from Set 17 verified data files. The graph must contain:

**Node types:**
```python
ChampionNode: {id, name, cost: 1-5, traits: List[TraitName], ability_summary, role, items_ideal}
ItemNode: {id, name, category: component|standard|radient|emblem|artifact, stats, effect_text}
TraitNode: {id, name, type: origin|class, breakpoints: Dict[int,str], description}
AugmentNode: {id, name, tier: Silver|Gold|Prismatic, description, relevant_champions}
GodNode: {id, name, title, focus, reward_tiers}
SystemNode: {id, name, description, mechanics}
```

**Edge types:**
```
HAS_TRAIT(champion_id, trait_id, count: int)
BUILDS_FROM(item_id, component_a, component_b)
ITEM_FOR_CHAMPION(item_id, champion_id)    # best-in-slot or common item
SYNERGIZES(champion_id_a, champion_id_b)  # meta pairings
TRAIT_BREAKPOINT(trait_id, count, bonus_text)
GOD_ALIGNMENT(god_id, trait_id, focus_category)
COUNTERS(champion_id, champion_id)         # from meta data
ITEM_INTO(item_id, upgraded_item_id)      # component → full item
```

**Data sources for graph construction:**
- `augments_full_user_verified.json` → AugmentNode (252 augments)
- `traits_full_user_verified.json` → TraitNode (30+ traits)
- `items_effects_expanded_set17.json` → ItemNode (45+ items)
- `tft_set17_patch17_1_deep_pack_v4_user_verified.json` → ChampionNode + SystemNode (59 champions)
- `tft_set17_patch17_1_enhanced_pack.json` → GodNode + SystemNode
- `tft_set17_patch17_1_data_pack.json` → champion ability summaries, system descriptions
- `rolling_odds_user_verified.json` → SystemNode (rolling odds)

**Validation:** Graph must have ≥ 59 ChampionNode, ≥ 30 TraitNode, ≥ 45 ItemNode, ≥ 252 AugmentNode after initial load. Print counts on startup.

---

#### KNOW-02: Graph API Endpoints
**Phase:** 11 | **Plan:** 11-02

Expose FastAPI endpoints for graph queries:

**`GET /api/graph/query`**
```
Query params:
  - entity: str (required) — node name to query
  - relation: str (optional) — edge type (e.g. "HAS_TRAIT", "ITEM_FOR_CHAMPION")
  - depth: int (default=1, max=3) — traversal depth
  - limit: int (default=10) — max results

Response:
{
  "entity": "Briar",
  "query": "neighbors",
  "results": [
    {"type": "ITEM_FOR_CHAMPION", "target": "Bloodthirster", "metadata": {"role": "carry"}},
    {"type": "HAS_TRAIT", "target": "Anima", "count": 1},
    {"type": "SYNERGIZES", "target": "Jinx", "metadata": {"reason": "meta_pair"}}
  ],
  "total": 8
}
```

**`GET /api/graph/neighbors/{entity_name}`**
```
Query params:
  - types: List[str] (optional) — filter by node type (champion, item, trait, augment)
  - limit: int (default=10)

Response:
{
  "entity": "Anima",
  "neighbors": [
    {"node": "Briar", "type": "champion", "edge": "HAS_TRAIT", "count": 1},
    {"node": "Jinx", "type": "champion", "edge": "HAS_TRAIT", "count": 1},
    {"node": "Anima Weapons", "type": "system", "edge": "TRAIT_BREAKPOINT", "bonus": "Start Researching!"}
  ]
}
```

**`POST /api/graph/ingest`**
```
Request: { "source": "all" | "augments" | "champions" | "items" | "traits" | "systems" }
Response: { "reloaded": true, "node_counts": {...}, "timestamp": "..." }
```

**Error handling:** Return 404 if entity not found with suggestion: `{"error": "Entity not found", "suggestions": ["Briar", "Jinx", "Illaoi"]}`

---

#### KNOW-03: Auto-reload on Patch Ingest
**Phase:** 11 | **Plan:** 11-03

The knowledge graph must reload when new patch data is ingested:

1. **Event-driven reload:** When `POST /api/ingest/patch-notes` or `POST /api/ingest/metatft` completes successfully, emit an internal event that triggers graph reload
2. **Hot-reload endpoint:** `POST /api/graph/reload` — reloads graph from JSON files without restarting the server
3. **Cache invalidation:** After reload, clear the embedding cache (`embedding_cache.clear()`) since new chunks may change retrieval rankings
4. **Startup load:** Graph loads on backend startup (lazy-load, not blocking startup)
5. **Reload notification:** After reload, emit SSE event `{"type": "graph_reloaded", "timestamp": "..."}` on a `/api/graph/events` endpoint (optional — frontend can poll or ignore)

---

#### KNOW-04: Unit Tests for Graph Traversals
**Phase:** 11 | **Plan:** 11-04

Comprehensive test coverage for knowledge graph:

```python
class TestKnowledgeGraph:
    def test_graph_loads_with_all_node_types(self)
    def test_graph_has_minimum_node_counts(self)  # ≥59 champion, ≥30 trait, ≥45 item, ≥252 augment
    def test_has_trait_edges_correct_count(self)   # Briar → Anima = 1
    def test_neighbor_query_returns_neighbors(self)
    def test_neighbor_query_filters_by_type(self)
    def test_missing_entity_returns_404(self)
    def test_graph_reload_preserves_structure(self)
    def test_circular_references_handled(self)     # A synergizes B, B synergizes A
    def test_empty_champion_traits_handled(self)   # champions with no traits edge
    def test_depth_3_traversal_no_infinite_loop(self)
```

**Test data:** Use fixture JSON files derived from the verified data packs (not live production data). Tests must run in <5 seconds.

---

### Phase 12: UI/UX Core Redesign (UI-01..05)

#### UI-01: Layout Refactor — Overflow Fix
**Phase:** 12 | **Plan:** 12-01

Fix all layout overflow issues identified from the UI screenshot:

**Root cause fixes:**
1. `MessageList.tsx` container: add `min-w-0` to prevent flex children from exceeding bounds
2. Message bubble wrapper: `max-w-[70%]` on bubble AND parent flex column with `overflow-x-hidden`
3. `ChatShell` main area: add `min-w-0` to the `flex-1` container
4. Message content: `overflow-wrap: break-word; word-break: break-word` on prose containers
5. Code blocks and long URLs: `overflow-x: auto; max-width: 100%` for tables and code
6. Citation cards grid: use CSS Grid with `minmax(0, 1fr)` columns instead of auto
7. Streaming messages: ensure cursor stays visible, text wraps at viewport edge

**Acceptance criteria:**
- [ ] Long messages wrap at viewport edge (no horizontal scroll on chat area)
- [ ] Message bubbles stay within 70% width of chat container
- [ ] Sidebar does not shift when long messages appear
- [ ] Code blocks and URLs scroll horizontally instead of stretching container
- [ ] CompCard and CitationCard stay within bubble bounds

---

#### UI-02: CitationCard v2 — Expandable & Filterable
**Phase:** 12 | **Plan:** 12-02

Upgrade CitationCard from basic card to interactive component:

**Features:**
- **Collapsed mode:** Show source name + match percentage + first line of text (line-clamp-2)
- **Expanded mode:** Click to expand, show full citation text with `max-height` transition
- **Source filter:** Dropdown or tabs to filter citations by source (metatft, obsidian, patch_notes, etc.)
- **Score indicator:** Visual bar or color-coded score (green >80%, yellow 50-80%, gray <50%)
- **Copy button:** Copy citation text to clipboard
- **Relevance sorting:** Citations sorted by score descending

**Transitions:** Smooth `max-height` transition (300ms ease) between collapsed/expanded states.

---

#### UI-03: CompCard Tailwind Migration + Type Safety
**Phase:** 12 | **Plan:** 12-03

Replace inline styles in `CompCard.tsx` with Tailwind classes and add full type safety:

**Migration:**
- Convert all inline `style={{...}}` objects to Tailwind className
- Use Tailwind color system (use `ring-` and `bg-` variants instead of rgba hardcoding)
- Extract color constants to a `tierColors` Tailwind config extension

**Type safety:**
- PropTypes → TypeScript interface (already done, verify completeness)
- `tier` prop: `'S' | 'A' | 'B'` with exhaustive switch/case
- `items` prop: array of validated item names
- `units` prop: array of champion name strings
- `traits` prop: `Array<{name: string; count: number}>`

**New features:**
- Tier badge with glow effect for S-tier (use `shadow-[color]/[opacity]`)
- Responsive: stack stats vertically on mobile, horizontal on desktop
- Item count indicator: show "3/3" progress for complete vs partial items
- Carry champion highlighted with gradient border

---

#### UI-04: Responsive Breakpoints
**Phase:** 12 | **Plan:** 12-04

Implement responsive layout for tablet and mobile:

**Breakpoints:**
- `sm` (640px+): Current desktop layout
- `md` (768px+): Sidebar 56 (w-56), ModeTabs larger
- `lg` (1024px+): Full layout with hover states
- Below `sm`: Mobile — sidebar hidden by default, hamburger menu toggle

**Mobile features:**
- Sidebar: slide-in drawer from left with backdrop overlay
- Hamburger menu button in header (only visible below 640px)
- ModeTabs: full-width tabs on mobile, wrap if needed
- Message bubbles: `max-w-[85%]` on mobile (more space)
- Touch targets: minimum 44x44px for all buttons
- Swipe-to-delete on session list items (optional enhancement)

**Tablet features:**
- Sidebar 240px (w-60)
- Better use of horizontal space for CitationCard grids (2 columns on tablet)

---

#### UI-05: Loading States + Streaming UX Polish
**Phase:** 12 | **Plan:** 12-05

Polish all loading and streaming states:

**Session loading:**
- Skeleton loader for session list (3 placeholder items with shimmer animation)
- Skeleton loader for message history

**Streaming UX:**
- Improve typing indicator: 3 dots with staggered bounce, but also show a subtle "thinking" pulse
- Progressive text reveal: messages appear token by token (already works, verify no jank)
- Streaming cursor: blinking cursor at end of streaming message
- "Generating..." label while streaming (subtle, non-intrusive)

**Composer polish:**
- Character count indicator for long messages (subtle, bottom-right of textarea)
- Disabled state: clearly dimmed with tooltip explaining why
- Send button: loading spinner inside button while preparing request
- Error state: red border on textarea, error message below

**Empty welcome screen:**
- Add TFT theming: gradient background, TFT logo/icon
- Quick-start suggestions: 3 clickable example questions
- Patch version badge and GPU status visible

---

### Phase 13: Smart Chat Engine (SMART-01..05)

#### SMART-01: Smart Entity JSON Markers + Frontend Parser
**Phase:** 13 | **Plan:** 13-01

Enable the LLM to emit structured entity markers that the frontend renders as rich cards:

**Marker format in LLM response:**
```
Here's what you need to know about Soraka:

{"type": "champion", "name": "Soraka", "cost": 3, "traits": [{"name": "Divine", "count": 1}, {"name": "Invoker", "count": 2}], "ability": "Wish", "role": "support"}

Soraka works well with HP items:

{"type": "item", "name": "Warmog's Armor", "category": "Tank", "stats": ["+800 HP"], "effect": "Gain 5 HP per second. Restore 25% max HP when below 30%."}

Key trait breakpoints:

{"type": "trait", "name": "Divine", "count": 3, "bonus": "Your Divines gain 30% damage amp"}
```

**Frontend parser in MessageList:**
- Regex scan for `{"type": "champion"|"item"|"trait"|"augment"|"augment_card"|"system"}` JSON blocks
- Extract JSON, validate schema, render appropriate entity card
- Fallback: if JSON invalid, render as code block
- Streaming: parse incrementally as tokens arrive, render cards progressively

**LLM prompt update:**
Add to RAG mode system prompt:
```
When answering questions about specific champions, items, traits, or augments, emit structured JSON markers at the relevant point in your response. Format:
{"type": "champion", "name": "...", "cost": N, "traits": [{"name": "...", "count": N}], "ability": "...", "role": "..."}
{"type": "item", "name": "...", "category": "AD|AP|Tank|Support", "stats": ["..."], "effect": "..."}
{"type": "trait", "name": "...", "count": N, "bonus": "..."}
{"type": "augment", "name": "...", "tier": "Silver|Gold|Prismatic", "effect": "..."}
```

---

#### SMART-02: Inline Entity Card Components
**Phase:** 13 | **Plan:** 13-02

Build rich, themed card components for each entity type:

**ChampionProfile:**
- Champion name + cost badge (colored by cost: 1=gray, 2=green, 3=blue, 4=purple, 5=gold)
- Trait badges (colored by trait type)
- Ability name + brief summary
- Ideal items (3 slots, show empty slots for build path)
- HP/AD/AP stats if available
- Compact horizontal layout: `[CostBadge] Name | [TraitBadge] [TraitBadge] | Ability: X`

**ItemCard:**
- Item name + category badge (AD=red, AP=blue, Tank=green, Support=purple)
- Component recipe (e.g., "B.F. Sword + Giant's Belt")
- Stats provided
- Effect text (expandable if long)
- Item icon placeholder (text-based: "⚔️" for AD, "🔮" for AP, etc.)

**TraitCard:**
- Trait name + type badge (Origin/Class)
- Tier badges with active count highlighted
- Description text
- Champions with this trait (grid of small champion badges)
- Breakpoint bonuses (current active breakpoint highlighted)

**AugmentCard:**
- Augment name + tier badge (Silver/Gold/Prismatic with color)
- Tier description (Silver: 1-3, Gold: 4-5, Prismatic: 6+)
- Effect text
- Related champions (if applicable)

**Design:** All cards use a consistent dark theme matching the app's `gray-900` background. Cards have subtle borders, hover lift effect, and click-to-expand for details.

---

#### SMART-03: Smart Reply Suggestions
**Phase:** 13 | **Plan:** 13-03

Add context-aware reply suggestion chips above the Composer:

**Suggestion generation:**
- After user sends a message, call `GET /api/graph/suggest?context={message}&limit=3`
- Backend uses knowledge graph to generate relevant suggestions based on entities in the message
- Example: User asks "best items for Briar?" → suggestions: "See Anima trait breakdown", "Top 3 S-tier comps with Briar", "Briar ability details"

**UI:**
- 2-3 horizontal chips above the Composer input
- Each chip: text + subtle arrow icon
- Click to auto-fill and send the suggestion
- Dismissible with X button
- Fade-in animation on appearance (200ms)
- Fallback: if `/api/graph/suggest` fails, show static suggestions from hardcoded list

**Static fallback suggestions:**
- "Top comps this patch?" (→ MetaTFT query)
- "Best augments for early game?" (→ Augment query)
- "How does Anima work?" (→ Trait query)

---

#### SMART-04: Cross-Entity Query Routing
**Phase:** 13 | **Plan:** 13-04

Intelligent routing that decides whether to use Knowledge Graph, RAG, or MetaTFT based on query intent:

**Routing matrix:**
```
Query pattern → Primary source → Fallback

"best items for {champion}?"     → Knowledge Graph (neighbors) → RAG
"{champion} stats/ability/role?" → Knowledge Graph → RAG
"{trait} breakpoints/bonus?"     → Knowledge Graph → RAG
"what traits go with {champion}?"→ Knowledge Graph → RAG
"is {trait} good?"               → Knowledge Graph + RAG (patch context) → RAG only
"top comps?" / "best comp?"      → RAG (MetaTFT chunks) → Knowledge Graph
"{augment} worth taking?"        → RAG → Knowledge Graph (augment node)
"rolling odds at level {N}?"     → Knowledge Graph (SystemNode: rolling_odds) → RAG
"compare {item} vs {item}?"      → Knowledge Graph (ItemNode) → RAG
"{champion} vs {champion}?"      → Knowledge Graph + RAG (meta) → RAG only
"what changed in patch 17.1?"    → RAG (patch notes) → Knowledge Graph
"who is the {god} god?"          → Knowledge Graph (GodNode) → RAG
"Realm of the Gods how?"         → Knowledge Graph (SystemNode) → RAG
```

**Implementation:**
- FastAPI dependency: `QueryRouter` class that classifies the query
- Call primary source → if results insufficient (< 2 chunks or low confidence), call fallback
- Merge results, deduplicate, rank by confidence
- Return combined context to LLM with source attribution

---

#### SMART-05: Coach Mode Enhancement
**Phase:** 13 | **Plan:** 13-05

Upgrade Coach mode with pivot chains and in-game scenario presets:

**Pivot fallback chain:**
Add to Coach system prompt:
```
After presenting 2-3 lines of play, always include a pivot fallback:
"If {primary_comp} is contested or you're bleeding out, pivot to {pivot_comp} using shared {shared_units} units and {shared_items} items. Expected board at stage 5: {pivot_units}."
```

**In-game scenario presets:**
User can prepend their message with a scenario tag:
- `[fast8]` — Fast 8 roll: "What comp should I play if I hit level 8 with 50g and no pairs?"
- `[hyperoll]` — Hyperoll: "I'm hyperolling {champion}. What's my ideal items and backup plan?"
- `[1star]` — 1-star holding: "I'm holding a 5-cost. What board should I build around it?"
- `[lategame]` — Stage 5+: "I'm stage 5 with {HP}g HP. Full send or eco?"

The Coach recognizes these tags and adjusts its response framing (econ advice, tempo check, board cap analysis).

**Visual line-of-play cards:**
```
╔══════════════════════════════════════╗
║ 🎯 PRIMARY: Dark Star 6             ║
║ Econ: 30g after krugs → roll at 4-2║
║ Tempo: Stable at 6, fast 8 at 5-1  ║
║ Cap:   Kai'Sa 2★ + Mordekaiser 2★  ║
╚══════════════════════════════════════╝
```

---

### Phase 14: RAG 2.0 + Full Data Ingest (RAG2-01..05)

#### RAG2-01: Metadata Filtering by Entity Type
**Phase:** 14 | **Plan:** 14-01

Enhance the RAG retrieval pipeline with entity-type filtering:

**Schema change:**
Add `entity_type` column to `document_chunks`:
```sql
ALTER TABLE document_chunks ADD COLUMN entity_type TEXT
  GENERATED ALWAYS AS (metadata->>'entity_type') STORED;
CREATE INDEX idx_chunks_entity_type ON document_chunks(entity_type);
```

**Entity type values:** `champion`, `item`, `trait`, `augment`, `system`, `meta`, `patch_notes`, `general`

**Enhanced hybrid search function:**
```sql
CREATE OR REPLACE FUNCTION hybrid_search_chunks(
  query_embedding vector(1024),
  query_text text,
  top_k int,
  patch_filter text DEFAULT NULL,
  entity_filter text DEFAULT NULL  -- NEW
) RETURNS TABLE(...) AS $$
  -- existing RRF logic with additional WHERE clause for entity_filter
  WHERE (patch_filter IS NULL OR metadata->>'patch' = patch_filter)
    AND (entity_filter IS NULL OR metadata->>'entity_type' = entity_filter)
$$;
```

**API enhancement:**
`POST /search` and `POST /chat` accept optional `entity_filter` in request body.

---

#### RAG2-02: Heuristic Reranking
**Phase:** 14 | **Plan:** 14-02

Implement multi-factor ranking before returning chunks:

**Ranking formula:**
```
final_score = cosine_similarity × patch_priority × entity_priority × recency_boost
```

**Factors:**
```
patch_priority:
  current_patch (17.1) = 1.0
  previous_patch (17.0) = 0.7
  older = 0.3

entity_priority (for meta queries):
  champion > item > trait > augment > system > general
  (configurable per-query, defaults above)

recency_boost:
  ingested in last 7 days = 1.2
  ingested 7-30 days ago = 1.0
  ingested > 30 days ago = 0.8
```

**Implementation:**
- Apply ranking in Python after SQL fetch (before returning to LLM)
- Ranking weights configurable via `settings.ranking_weights` dict
- Log ranking decision for debugging: `{"chunk_id": "c123", "cosine": 0.87, "patch_prio": 1.0, "entity_prio": 1.2, "final": 1.044}`

---

#### RAG2-03: Streaming Citations
**Phase:** 14 | **Plan:** 14-03

Enable citations to appear progressively during streaming:

**SSE event types:**
```python
# Before streaming starts, indicate citations are incoming
{"type": "citation_start", "data": {"id": "c1", "source": "metatft", "heading": "S-Tier Comps"}}

# Citation content resolves as response streams
{"type": "citation_progress", "data": {"id": "c1", "text_preview": "Briar carry comp..."}}

# After streaming completes, finalize citation
{"type": "citation_end", "data": {"id": "c1", "text": "Briar is the top S-tier carry...", "score": 0.91}}

# If streaming is aborted
{"type": "citation_abort", "data": {"id": "c1"}}
```

**Frontend handling:**
- `citation_start` → Show a "streaming source" badge next to the message, pulsing
- `citation_progress` → Show preview text in the badge
- `citation_end` → Convert badge to full CitationCard
- `citation_abort` → Remove the badge

**Non-streaming mode:** Citations appear at the end as before (backward compatible).

---

#### RAG2-04: Full Ingest Pipeline
**Phase:** 14 | **Plan:** 14-04

Ingest all verified data files into the vector DB with proper metadata:

**Source → Chunks mapping:**

**augments_full_user_verified.json (252 augments):**
- Split by tier (Silver/Gold/Prismatic) then by effect groups
- ~200 chars per chunk, 50% overlap
- Metadata: `{entity_type: "augment", tier, relevant_round: "1-3|4-5|6+", set: 17, patch: "17.1"}`
- Target: ~180 chunks

**traits_full_user_verified.json (30+ traits):**
- One chunk per trait (description + champions + breakpoints)
- ~300 chars per chunk
- Metadata: `{entity_type: "trait", category: origin|class, set: 17, patch: "17.1"}`
- Target: ~35 chunks

**items_effects_expanded_set17.json (45+ items):**
- One chunk per item (effect + stats + recipe)
- ~300 chars per chunk
- Metadata: `{entity_type: "item", category, set: 17, patch: "17.1"}`
- Target: ~50 chunks

**tft_set17_patch17_1_deep_pack_v4_user_verified.json:**
- Champions: ability summaries + trait assignments + role
- Systems: Realm of the Gods, Space Gods, Anima Weapons, etc.
- ~400 chars per chunk
- Metadata: `{entity_type: "champion"|"system", cost, traits[], set: 17, patch: "17.1"}`
- Target: ~100 chunks

**tft_set17_patch17_1_enhanced_pack.json:**
- Space Gods system: 9 gods with reward tiers, Boon armory mechanics
- ~300 chars per god
- Target: ~20 chunks

**rolling_odds_user_verified.json:**
- Rolling odds table by level
- ~200 chars (compact format)
- Metadata: `{entity_type: "system", system: "rolling", set: 17, patch: "17.1"}`
- Target: ~10 chunks

**Total target: ≥ 500 high-quality chunks with entity_type metadata**

**Ingest validation:**
- Count chunks per entity_type after ingest
- Verify no duplicate content (hash-based dedup)
- Log chunk counts per source to console

---

#### RAG2-05: Obsidian File Watcher
**Phase:** 14 | **Plan:** 14-05

Implement real-time reactive sync for Obsidian vault files:

**Implementation options (pick one based on feasibility):**
1. **Polling watcher:** `POST /api/watch/start` — background thread polls Obsidian vault every 30 seconds, diffs file hashes, triggers re-ingest for changed files
2. **Filesystem watcher:** Use `watchdog` library to subscribe to filesystem events on the vault directory

**API:**
```
POST /api/watch/start
  Request: { "vault_path": "C:\\path\\to\\vault" }
  Response: { "watching": true, "files": 42, "started_at": "..." }

POST /api/watch/stop
  Response: { "watching": false }

GET /api/watch/status
  Response: { "watching": true, "last_event": "...", "events_count": 5 }
```

**Event log:**
```python
{
  "event": "file_changed",
  "path": "TFT Notes\\Set 17\\Anima Comp Guide.md",
  "hash": "abc123",
  "action": "re-ingested",
  "timestamp": "2026-04-23T12:00:00Z"
}
```

---

## Traceability Matrix

| REQ-ID | Phase | Plan | Status |
|--------|-------|------|--------|
| KNOW-01 | 11 | 11-01 | ✅ 9cdcc66 |
| KNOW-02 | 11 | 11-02 | ✅ 9cdcc66 |
| KNOW-03 | 11 | 11-03 | ✅ 9cdcc66 |
| KNOW-04 | 11 | 11-04 | ✅ 9cdcc66 |
| UI-01 | 12 | 12-01 | ✅ 2026-04-23 |
| UI-02 | 12 | 12-02 | ✅ 2026-04-23 |
| UI-03 | 12 | 12-03 | ✅ 2026-04-23 |
| UI-04 | 12 | 12-04 | ✅ 2026-04-23 |
| UI-05 | 12 | 12-05 | ✅ 2026-04-23 |
| SMART-01 | 13 | 13-01 | 📋 |
| SMART-02 | 13 | 13-02 | 📋 |
| SMART-03 | 13 | 13-03 | 📋 |
| SMART-04 | 13 | 13-04 | 📋 |
| SMART-05 | 13 | 13-05 | 📋 |
| RAG2-01 | 14 | 14-01 | 📋 |
| RAG2-02 | 14 | 14-02 | 📋 |
| RAG2-03 | 14 | 14-03 | 📋 |
| RAG2-04 | 14 | 14-04 | 📋 |
| RAG2-05 | 14 | 14-05 | 📋 |

**Total v1.4 requirements:** 19
**v1.0 + v1.1 + v1.2 + v1.3 requirements:** 35 + 5 + 5 + 5 = 50

---

## Deferred to Future Milestones

### v2 Requirements (Not in v1.4)
| REQ-ID | Description |
|---------|-------------|
| MODEL-01 | gemma3:12b for Coach mode, qwen3:8b for Normal/RAG |
| MODEL-02 | Query embedding cache (30-min TTL) — already implemented in v1.0 |
| SESS-01 | Session auto-naming from first message |
| SESS-02 | Session search by keyword |
| SESS-03 | Session export as Markdown to Obsidian |
| SESS-04 | Cross-session memory from past conversations |
| RAG-10 | Retrieval debug panel showing chunks, scores, sources |
| RAG-11 | Heuristic reranking (patch priority) — RAG2-02 covers this |
| PROMPT-04 | Visual line-of-play cards with icons — SMART-05 covers this |
| PROMPT-06 | In-game scenario presets — SMART-05 covers this |
| EVAL-01 | Smoke test suite with scoring |
| EVAL-02 | Retrieval quality metrics (recall@K) |
| EVAL-03 | Structured logging for every request |

---

*Requirements defined: 2026-04-23*
*v1.4 "Smart & Polished" — 19 requirements across Phases 11-14*
