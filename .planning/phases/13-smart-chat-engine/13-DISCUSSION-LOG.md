# Phase 13: Smart Chat Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 13-smart-chat-engine
**Areas discussed:** JSON Parser, Card Design System, Suggestion Chips, Query Router, Coach Mode

---

## JSON Parser

| Option | Description | Selected |
|--------|-------------|----------|
| Incremental parse | Parse each marker as it appears in stream | |
| Full parse | Parse after full response | |
| Hybrid — buffer then parse | Buffer fragments until complete JSON object | |

**User's choice:** (agent's discretion — not explicitly discussed)
**Notes:** User skipped this area in discussion. Agent discretion on parse mode.

---

## Card Design System

### Theme

| Option | Description | Selected |
|--------|-------------|----------|
| Cosmic/Space Gods | Full cosmic theme — gradients, glows, purple/blue | |
| Minimal clean | Flat design, borders clear, no glows | |
| **Hybrid — cosmic accents, minimal layout** | Cosmic color palette but clean card structure | ✅ |

**User's choice:** "chọn a nhưng không quá nhiều đủ để biết là mùa gì nhưng vẫn ấn tượng"
**Notes:** User wants cosmic theme but not overwhelming — enough to know the season but still impressive. "Đủ để biết là mùa gì nhưng vẫn ấn tượng"

### Champion Cost Display

| Option | Description | Selected |
|--------|-------------|----------|
| Cost badge | Colored box/gem with number (★ × cost or ◆ × cost) | |
| **Tier-colored text** | Text color by cost tier (1=gray, 2=green, 3=blue, 4=purple, 5=gold) | ✅ |
| Both | Badge icon AND colored text | |

**User's choice:** tier_color
**Notes:** Simpler, cleaner approach — no badge icons needed

### Item Category Display

| Option | Description | Selected |
|--------|-------------|----------|
| Emoji-based icons | ⚔️ AP, 🛡️ Tank, etc. | |
| **Color-coded category badge** | AD=red, AP=blue, Tank=green, Support=purple | ✅ |
| Text-only | Text label only | |

**User's choice:** color_badge
**Notes:** Matches the cosmic/minimal hybrid approach

---

## Suggestion Chips

### Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Above Composer | Between MessageList and input — scrolls away | |
| Below Composer | Inside Composer container, flush with input | |
| **Sticky above Composer** | Always visible, does not scroll away | ✅ |

**User's choice:** sticky
**Notes:** Always accessible — user can always see and use suggestions

---

## Query Router

### Routing Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Keyword/pattern matching | Regex/keywords to classify query type | |
| LLM-based classifier | Small LLM to classify query intent | |
| **Graph-first, RAG fallback, MetaTFT enrichment** | Graph for entities, RAG for complex, MetaTFT for meta | ✅ |

**User's choice:** graph_fallback
**Notes:** Aligns with locked decision in PROJECT.md (graph-first routing)

### Result Merging

| Option | Description | Selected |
|--------|-------------|----------|
| Merge all | Combine all results with source attribution | ✅ |
| Primary only | Use primary source only | |
| Merge if threshold | Use primary, add secondary if < 2 results | |

**User's choice:** merge
**Notes:** Best of all worlds — leverage multiple sources when available

---

## Coach Mode

### Visual Format

| Option | Description | Selected |
|--------|-------------|----------|
| **Line-of-play cards** | Visual box/card layout for each line of play | ✅ |
| Enhanced markdown | Bold, borders, emoji for sections | |
| Hybrid | Simple=markdown, complex=cards | |

**User's choice:** line_cards
**Notes:** Visual format makes the primary/pivot distinction clear

### Scenario Preset Activation

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt prefix | [fast8] in message body | |
| Separate mode | Sub-mode option in UI | |
| **Both** | Tag prefix + mode option | ✅ |

**User's choice:** both
**Notes:** Flexibility for power users + quick access for casual users

---

## Agent's Discretion

The following were left to agent discretion during implementation:
- Exact CSS values for cosmic accent colors
- Exact component file structure (single file per card vs shared base)
- Whether to use `dangerouslySetInnerHTML` or React parsing for markdown text in cards
- Suggestion chip max-width and truncation strategy
- Router confidence threshold for merging secondary sources

---

## Deferred Ideas

- Phase 14: Streaming citations (RAG2-03)
- Phase 14: Obsidian file watcher (RAG2-05)
- Phase 14: Metadata entity type filtering (RAG2-01)
- v2: Model upgrade to qwen3:8b or gemma3:12b (MODEL-01)
- v2: Session export to Obsidian (SESS-03)
- v2: Cross-session memory (SESS-04)
- v2: Retrieval debug panel (RAG-10)
- v2: Eval/observability suite (EVAL-01..03)
