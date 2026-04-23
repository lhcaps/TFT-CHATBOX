# Phase 13: Smart Chat Engine — UI Design Contract

**Phase:** 13
**Generated:** 2026-04-23
**Status:** Ready for planning
**Source:** $gsd-discuss-phase 13 — decisions captured in 13-CONTEXT.md

---

## 1. Concept & Vision

The Smart Chat Engine renders TFT knowledge as **rich inline entity cards** — not walls of text. Each card is a compact, themed snapshot of a champion, item, trait, or augment that appears right where the LLM mentions it. The aesthetic continues the Space Gods cosmic theme from Phase 12: **cosmic accents on minimal layout** — enough to know this is Set 17, but clean enough to stay scannable in a chat thread.

**Tone:** Premium knowledge cards floating in a cosmic void. 4-cost and 5-cost champions glow with subtle border-pulse animation (framer-motion) — signaling their rarity and power.

---

## 2. Design Language

### Aesthetic Direction
**Cosmic minimal** — cosmic color palette (purple/blue hues) and themed icons on a clean, flat card structure. NOT full cosmic gradient backgrounds. Reference: Notion AI cards, Linear's entity popovers, Raycast's inline results.

### Color Palette (extends Phase 12)

|| Role | Color | Tailwind / Hex |
|------|-------|----------------|
| Background base | Deep charcoal | `bg-gray-950` `#0a0a0f` |
| Background surface | Dark gray | `bg-gray-900` `#111827` |
| Card surface | Elevated gray | `bg-gray-800/80` |
| Card border | Subtle purple | `border-purple-500/30` |
| **Glow pulse (4-5 cost)** | **Purple-400 → Purple-300** | **`#c084fc → #d8b4fe`** |
| Text primary | Gray-100 | `text-gray-100` |
| Text secondary | Gray-400 | `text-gray-400` |
| Champion cost: 1 | Gray | `text-gray-400` |
| Champion cost: 2 | Green | `text-green-400` |
| Champion cost: 3 | Blue | `text-blue-400` |
| Champion cost: 4 | Purple | `text-purple-400` |
| Champion cost: 5 | Gold | `text-yellow-400` |
| Item AD | Red | `text-red-400` / `bg-red-900/50` |
| Item AP | Blue | `text-blue-400` / `bg-blue-900/50` |
| Item Tank | Green | `text-green-400` / `bg-green-900/50` |
| Item Support | Purple | `text-purple-400` / `bg-purple-900/50` |
| Augment Silver | Gray-300 | `text-gray-300` / `bg-gray-700` |
| Augment Gold | Yellow-400 | `text-yellow-400` / `bg-yellow-900/50` |
| Augment Prismatic | Pink-400 | `text-pink-400` / `bg-pink-900/50` |
| Trait Origin | Indigo | `text-indigo-400` / `bg-indigo-900/50` |
| Trait Class | Cyan | `text-cyan-400` / `bg-cyan-900/50` |

### Typography
- **Primary:** `Inter` / `system-ui` — clean, legible
- **Mono:** `JetBrains Mono` / `monospace` — item names, champion names
- **Scale:** Tailwind defaults (`text-xs` 12px, `text-sm` 14px, `text-base` 16px)

### Spatial System
- Base unit: 4px (Tailwind default)
- Card padding: `p-3` (12px)
- Card gap: `gap-2` (8px)
- Badge padding: `px-2 py-0.5` (8px / 4px)
- Section spacing: 24px

### Motion Philosophy
- **Glow pulse (4-5 cost champions):** framer-motion `animate` — border color pulses between `border-purple-400` and `border-purple-300` on a **2.5s loop**, infinite. Target: `border` property with CSS keyframes.
- **Suggestion chips:** 200ms fade-in on appearance
- **Card hover:** 150ms `ease-out` translateY(-1px) + shadow increase
- **Streaming card render:** Cards appear as markers complete — no dramatic animation, just fade-in
- **No bounce or spring** — calm, professional

### Visual Assets
- **Icons:** Lucide React (already in project)
  - Graph/Knowledge: `Network` icon — for hard knowledge source
  - Document: `FileText` icon — for RAG/patch notes source
  - MetaTFT: Custom inline SVG (MetaTFT logo) — for meta data source
- **No emoji in cards** — SVG icons only

---

## 3. Layout & Structure

### Entity Card Placement
Entity cards appear **inline within the message bubble**, parsed from JSON markers in the LLM text stream. Positioned where the JSON marker appears in the response flow.

```
┌─────────────────────────────────────────────┐
│ Assistant message bubble (gray-800)         │
│                                             │
│ Here's what you need to know about Soraka:  │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ [ChampionProfile Card]                    │ │
│ │ Champion name | 3-cost | Divine 1 Invoker│ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ HP items work great:                        │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ [ItemCard] Warmog's Armor | Tank | ...  │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Card Layout in Chat Thread
- Cards are block-level elements (not inline with text)
- Max-width: `max-w-[360px]` — compact enough to not dominate chat
- Stack vertically when multiple cards appear
- Source attribution icon badge in card footer (right-aligned)

### Suggestion Chips Layout
```
┌──────────────────────────────────────────────────────────┐
│ STICKY BAR (above Composer, always visible)             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │ See Anima →  │ │ Briar comps→ │ │ Augments? → │    │
│ └──────────────┘ └──────────────┘ └──────────────┘    │
│ [X] [X] [X]                                              │
└──────────────────────────────────────────────────────────┘
```
- **Position:** `sticky top-0 z-10` above Composer
- **Background:** `bg-gray-900/95 backdrop-blur border-b border-gray-800`
- **Chips:** `px-3 py-1.5 rounded-full bg-purple-900/50 text-purple-300 border border-purple-500/30`
- **Hover:** `bg-purple-800/50`
- **Dismiss:** Small X button on right of each chip

### Line-of-Play Card (Coach Mode)
```
╔══════════════════════════════════════╗
║ 🎯 PRIMARY: Dark Star 6             ║
║ Econ: 30g after krugs → roll at 4-2 ║
║ Cap:   Kai'Sa 2★ + Mordekaiser 2★ ║
║ ──────────────────────────────────── ║
║ ↪ PIVOT: 4 Anima if contested       ║
╚══════════════════════════════════════╝
```
- Visual box card with border (purple accent)
- Primary line vs pivot line clearly separated
- Icon: inline SVG target icon (`◉` or Lucide `Crosshair`)

---

## 4. Features & Interactions

### JSON Marker Parsing (streaming)
- Regex scan for `{"type": "champion"|"item"|"trait"|"augment"}` JSON blocks in SSE token stream
- Buffer until complete `{...}` detected
- Parse and render card incrementally (progressive reveal)
- Malformed JSON: render as `<code>` block
- Existing `MessageContent` component in MessageList.tsx extended to handle entity cards

### Entity Cards — Inline Rendering
- Cards rendered as React components within the message bubble
- Source attribution icon in bottom-right of each card
  - Graph icon (Network) → hard knowledge
  - Document icon (FileText) → RAG/patch notes
  - MetaTFT SVG → meta data
- Cards are clickable: expand to show full details (for champions, items with long effects)

### ChampionProfile Card
- Compact horizontal layout: `[Name (cost-colored)] | [TraitBadge] [TraitBadge] | Ability: X`
- Cost: **tier-colored text only** (no badge icon)
  - 4-cost: `text-purple-400` + **framer-motion glow pulse** on border
  - 5-cost: `text-yellow-400` + **framer-motion glow pulse** on border
- Trait badges: small colored pills
- Hover: lift + shadow

### ItemCard
- Category: **color-coded badge** (AD=red, AP=blue, Tank=green, Support=purple)
- Recipe shown as "Component A + Component B" in muted text
- Stats list
- Effect text (expandable if > 3 lines)
- Source icon in footer

### TraitCard
- Type badge: Origin (indigo) / Class (cyan)
- Champion list: small gray badges
- Breakpoint tiers: count badges (e.g., "3 ✦" highlighted if active)
- Source icon in footer

### AugmentCard
- Tier badge: Silver (gray-300) / Gold (yellow-400) / Prismatic (pink-400)
- Effect text
- Related champions as badges (if applicable)
- Source icon in footer

### Smart Reply Chips
- Sticky bar above Composer
- 2-3 chips per suggestion set
- Click: auto-fill Composer + send
- X button: dismiss chip
- Fade-in on appear (200ms)
- API: `GET /api/graph/suggest?context={msg}&limit=3`
- Fallback: hardcoded static suggestions if API fails

### Source Attribution Icons
- Small inline SVG icons next to information
- Size: `w-3 h-3` (12px) — subtle
- Position: bottom-right of card, or inline before text in compact views
- Tooltip on hover: "Source: Graph Knowledge" / "Source: Your Notes" / "Source: MetaTFT"

---

## 5. Component Inventory

### ChampionProfileCard
|| State | Appearance |
|-------|------------|
| Default (1-3 cost) | `bg-gray-800/80 border border-purple-500/30 rounded-lg p-3` |
| Default (4 cost) | Same + framer-motion glow pulse: `border-purple-400 → border-purple-300` 2.5s loop |
| Default (5 cost) | Same + glow pulse: `border-yellow-400 → border-yellow-300` 2.5s loop |
| Cost 1 | `text-gray-400` |
| Cost 2 | `text-green-400` |
| Cost 3 | `text-blue-400` |
| Cost 4 | `text-purple-400` |
| Cost 5 | `text-yellow-400` |
| Hover | `hover:-translate-y-0.5 hover:shadow-lg` |

### ItemCard
|| State | Appearance |
|-------|------------|
| Default | `bg-gray-800/80 border border-purple-500/30 rounded-lg p-3` |
| Category AD | `bg-red-900/50 border-l-2 border-red-500` |
| Category AP | `bg-blue-900/50 border-l-2 border-blue-500` |
| Category Tank | `bg-green-900/50 border-l-2 border-green-500` |
| Category Support | `bg-purple-900/50 border-l-2 border-purple-500` |

### TraitCard
|| State | Appearance |
|-------|------------|
| Default | `bg-gray-800/80 border border-purple-500/30 rounded-lg p-3` |
| Type Origin | `text-indigo-400 badge bg-indigo-900/50` |
| Type Class | `text-cyan-400 badge bg-cyan-900/50` |

### AugmentCard
|| State | Appearance |
|-------|------------|
| Default | `bg-gray-800/80 border border-purple-500/30 rounded-lg p-3` |
| Tier Silver | `text-gray-300 badge bg-gray-700` |
| Tier Gold | `text-yellow-400 badge bg-yellow-900/50` |
| Tier Prismatic | `text-pink-400 badge bg-pink-900/50` |

### SuggestionChip
|| State | Appearance |
|-------|------------|
| Default | `px-3 py-1.5 rounded-full bg-purple-900/50 text-purple-300 border border-purple-500/30` |
| Hover | `bg-purple-800/50 cursor-pointer` |
| Dismissed | Fade-out 200ms then remove |

### SourceIcon
|| Type | Icon |
|-------|------|------|
| Graph | Lucide `Network` (`w-3 h-3 text-purple-400`) |
| RAG | Lucide `FileText` (`w-3 h-3 text-blue-400`) |
| MetaTFT | Custom inline SVG — MetaTFT logo mark (`w-3 h-3`) |

### LineOfPlayCard (Coach)
|| State | Appearance |
|-------|------------|
| Primary | `border-l-4 border-purple-500 bg-purple-900/20 rounded p-3` |
| Pivot | `border-l-4 border-gray-600 bg-gray-800/50 rounded p-3 mt-2` |
| Header | Bold text with target icon |

---

## 6. Technical Approach

### Framework
- **React 18** + **Vite 6** + **Tailwind v4** (already in project)
- **framer-motion** — add as dependency for glow pulse animation
- Existing `~/` path alias for imports

### New Components to Create
```
apps/frontend/src/components/
  ChampionProfileCard.tsx   — NEW: champion entity card
  ItemCard.tsx             — NEW: item entity card
  TraitCard.tsx           — NEW: trait entity card
  AugmentCard.tsx         — NEW: augment entity card
  LineOfPlayCard.tsx      — NEW: coach mode visual cards
  SuggestionChips.tsx      — NEW: sticky suggestion chips bar
  SourceIcon.tsx           — NEW: source attribution icons (Graph/RAG/MetaTFT)
  EntityCardParser.tsx     — NEW: JSON marker parser + incremental renderer
```

### Key Files Modified
```
apps/frontend/src/components/
  MessageList.tsx           — Add EntityCardParser, render cards inline
  Composer.tsx             — Add SuggestionChips above textarea
apps/frontend/src/api/types.ts — Add EntityCard types, Suggestion type
apps/frontend/src/api/client.ts — Add suggest endpoint call
```

### Component Patterns
- All: TypeScript with strict types
- Props interfaces defined inline
- framer-motion `motion.div` for glow pulse on ChampionProfile
- Source icons: inline SVG components (no emoji)
- Source attribution: small badge in card footer

### Glow Animation Implementation
```tsx
// ChampionProfile glow for 4-5 cost
import { motion } from 'framer-motion';

<motion.div
  animate={{
    borderColor: cost === 5
      ? ['#c084fc', '#d8b4fe', '#c084fc']
      : ['#a855f7', '#c084fc', '#a855f7'],
  }}
  transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
  className="border-2 rounded-lg p-3 bg-gray-800/80"
>
  {/* card content */}
</motion.div>
```

### JSON Parser (EntityCardParser)
```tsx
// Streaming incremental parse in MessageList
// Regex: /\{\"type\":\s*\"(champion|item|trait|augment)\"[^}]+\}/g
// Buffer until complete JSON detected
// Render card immediately on complete JSON
// Malformed → <code> fallback
```

---

*UI-SPEC.md generated from discuss-phase decisions — all design decisions locked in 13-CONTEXT.md*
