# Phase 12: UI/UX Core Redesign — UI Design Contract

**Phase:** 12
**Generated:** 2026-04-23
**Status:** Ready for planning
**Source:** $gsd-discuss-phase 12 — 5 areas discussed, decisions captured in 12-CONTEXT.md

---

## 1. Concept & Vision

A polished, responsive TFT chat interface with a **Set 17 Space Gods** cosmic theme. The design feels like gazing into deep space — dark cosmic backgrounds, glowing accents, constellation-inspired icons. Every interaction should feel intentional and premium, befitting an intelligent knowledge companion for a competitive TFT player. The UI is clean and functional first, but with cosmic flourishes that make it memorable.

**Tone:** Sophisticated dark-space aesthetic. Not flashy — refined. Like a high-end astronomy app meets a premium strategy tool.

---

## 2. Design Language

### Aesthetic Direction
**Cosmic dark-space** — deep purples and blues, glowing accent borders, subtle gradient backgrounds. Reference: Space-themed dark UIs (Vercel dashboard dark, Linear dark mode, Raycast dark).

### Color Palette

| Role | Color | Hex / Tailwind |
|------|-------|---------------|
| Background base | Deep charcoal | `#0a0a0f` / `bg-gray-950` |
| Background surface | Dark gray | `#111827` / `bg-gray-900` |
| Surface elevated | Gray-800 | `#1f2937` / `bg-gray-800` |
| Border subtle | Gray-700 | `#374151` / `border-gray-700` |
| Border bright | Gray-600 | `#4b5563` / `border-gray-600` |
| Text primary | Gray-100 | `#f3f4f6` / `text-gray-100` |
| Text secondary | Gray-400 | `#9ca3af` / `text-gray-400` |
| Text muted | Gray-500 | `#6b7280` / `text-gray-500` |
| **Accent cosmic** | **Purple-500** | **`#a855f7`** / `text-purple-500` |
| **Accent glow** | **Purple-400** | **`#c084fc`** / `shadow-purple-400` |
| Tier S (gold) | Yellow-400 | `#fbbf24` / `text-yellow-400` |
| Tier A (silver) | Gray-300 | `#d1d5db` / `text-gray-300` |
| Tier B (bronze) | Orange-400 | `#fb923c` / `text-orange-400` |

### Typography
- **Primary:** `Inter` (system-ui fallback) — clean, legible
- **Mono:** `JetBrains Mono` / `monospace` — for item names in CompCard
- **Scale:** Tailwind defaults (`text-xs` 12px, `text-sm` 14px, `text-base` 16px)

### Spatial System
- Base unit: 4px (Tailwind default)
- Component padding: 12px / 16px (cards), 8px / 12px (badges)
- Section spacing: 24px between major sections
- Message bubble: `px-4 py-3`, gap between messages `space-y-4`

### Motion Philosophy
- **Transitions:** 150ms ease-out for hover states, 200ms for color changes
- **Drawer:** 300ms `ease-out` slide transition
- **Streaming cursor:** `animate-pulse` 1s infinite — subtle, not distracting
- **Modal:** Fade in backdrop 200ms, scale in content 150ms
- **No bounce or spring** — space is calm, not playful

### Visual Assets
- **Icons:** Lucide React (already in project) — consistent stroke weight
- **Custom SVG:** Constellation-style decorative icons for empty state
- **Backgrounds:** CSS gradient backgrounds, no images
- **Glow effects:** `shadow-[0_0_12px_rgba(168,85,247,0.25)]` for cosmic accents

---

## 3. Layout & Structure

### Overall Layout
```
┌──────────────────────────────────────────────────────────┐
│ SIDEBAR (w-64) │ HEADER (flex-1)                        │
│                 │  [Session Title]    [ModeTabs]           │
│ [New Chat]      ├──────────────────────────────────────────┤
│                 │ MESSAGE LIST (flex-1 overflow-y-auto)    │
│ [Session 1]     │                                          │
│ [Session 2]     │  [User bubble — right, blue-600]      │
│ [Session 3]     │  [Assistant bubble — left, gray-800]    │
│   ...          │  [CitationCards grid]                    │
│                 │  [CompCard — cosmic themed]              │
│                 ├──────────────────────────────────────────┤
│                 │ COMPOSER (border-t, bg-gray-800)        │
└─────────────────┴──────────────────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint | Width | Sidebar | Message Width |
|-----------|-------|---------|---------------|
| Mobile | <768px | Slide-in drawer (hamburger toggle) | 100% (`max-w-full`) |
| Tablet | 768-1023px | Collapsible panel | 90% (`max-w-[90%]`) |
| Desktop | ≥1024px | Fixed 256px | 70% (`max-w-[70%]`) |

### Sidebar Drawer (Mobile)
- **Trigger:** Hamburger button in header (appears only on mobile)
- **Animation:** Slide in from left, 300ms ease-out
- **Backdrop:** Semi-transparent black overlay (`bg-black/50`)
- **Close:** Tap backdrop or close button

### Header Layout
- **Old (fragile):** `<div className="w-64"><ModeTabs /></div>`
- **New (responsive):** `flex items-center gap-3` — no fixed width
- Mode tabs scale gracefully via flexbox

---

## 4. Features & Interactions

### Message Bubbles
- **Width:** Responsive via Tailwind `max-w-[70%] md:max-w-[90%] lg:max-w-[70%]`
- **Overflow:** `overflow-wrap: break-word` for URLs and code blocks
- **Container:** `min-w-0` on flex containers, `overflow-x-hidden` on parent
- **User messages:** Right-aligned, blue-600 background, rounded-br-md
- **Assistant messages:** Left-aligned, gray-800 background, rounded-bl-md
- **Markdown:** Rendered via `prose prose-invert prose-sm`

### CitationCard v2
- **Collapsed state:** Shows source (truncated) + heading (truncated) + 3 lines of text
- **Expand trigger:** Click anywhere on the card
- **Expanded state:** Modal overlay with full citation text
- **Modal:** Centered dialog, max-w-2xl, dark surface with backdrop blur
- **Source filter:** Dropdown above citation grid (All / Obsidian / Patch / MetaTFT)
- **Copy button:** Copy icon in modal header, copies full citation text

### CompCard (Migrated to Tailwind + Cosmic Theme)
- **Header:** Cosmic gradient border, tier badge with glow effect
- **Tier badge:** `text-yellow-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]` for S tier
- **Stats row:** Top4 rate + Avg Place in muted text
- **Items:** Color-coded pill badges (AD=red, AP=blue, Tank=green, Support=purple)
- **Units:** Small gray chips
- **Traits:** Colored chips matching tier color
- **NO inline styles** — 100% Tailwind utility classes
- **Responsive:** `max-w-[480px]` on desktop, scales on mobile

### Empty State (Cosmic Welcome Screen)
- **Background:** Multi-stop gradient `from-[#0f0c29] via-[#302b63] to-[#24243e]`
- **Icon:** Constellation SVG (custom inline SVG with star patterns)
- **Text:** Centered, `text-gray-400`, with subtle glow
- **Content:**
  - "Ask about TFT strategies, comps, augments, or patch notes."
  - "Switch modes above to search notes or get coaching."

### Streaming Indicator
- Three bouncing dots, `animate-bounce` (already in codebase)
- Purple tint: `bg-purple-500` instead of gray-400
- Subtle, doesn't distract from content

### Composer
- Auto-grow textarea: max-height 120px
- Enter to send, Shift+Enter for newline
- Send button disabled when empty or streaming
- **Mobile:** Full width, reduced padding

---

## 5. Component Inventory

### MessageBubble
| State | Appearance |
|-------|------------|
| Default | Gray-800 bg, max-w-[70%], prose text |
| User | Blue-600 bg, text-white, right-aligned |
| Streaming | Gray-800 bg, dots indicator |
| With citations | Citation grid below message text |

### CitationCard
| State | Appearance |
|-------|------------|
| Collapsed | Source + heading (truncated), 3-line text clamp, hover: border-gray-600 |
| Expanded (modal) | Full-screen overlay, dark bg, full text, copy button |
| Source filter | Dropdown above grid — All / Obsidian / Patch / MetaTFT |

### CompCard
| State | Appearance |
|-------|------------|
| Tier S | Gold gradient border, yellow glow badge |
| Tier A | Silver border, gray badge |
| Tier B | Bronze border, orange badge |
| Items (AD) | Red-tinted pill |
| Items (AP) | Blue-tinted pill |
| Items (Tank) | Green-tinted pill |
| Items (Sup) | Purple-tinted pill |

### Sidebar
| State | Appearance |
|-------|------------|
| Desktop | Fixed 256px, always visible |
| Tablet | Collapsible, toggle button visible |
| Mobile | Hidden, slide-in drawer on hamburger tap |

### EmptyState
| State | Appearance |
|-------|------------|
| Default | Cosmic gradient bg, constellation icon, centered text |

---

## 6. Technical Approach

### Framework
- **React 18** + **Vite 6** + **Tailwind v4** (already in project)
- No new dependencies — all CSS via Tailwind utilities
- Existing `~/` path alias (`@/` in tsconfig) for imports

### Key Files Modified
```
apps/frontend/src/components/
  ChatShell.tsx         — Responsive sidebar drawer, flex header
  MessageList.tsx       — overflow fix, responsive max-w
  CitationCard.tsx     — v2 with modal expand, source filter
  CompCard.tsx         — Full Tailwind rewrite, cosmic theme
  Composer.tsx         — Mobile padding adjustments
  EmptyState.tsx       — NEW: Cosmic welcome screen component
  CitationModal.tsx    — NEW: Modal component for CitationCard expand

apps/frontend/src/components/ui/
  button.tsx           — Already exists (shadcn)
  card.tsx            — Already exists (shadcn)
  dialog.tsx          — NEW: Optional shadcn Dialog for modal
```

### Responsive Strategy
- Tailwind responsive prefixes: `md:` (768px), `lg:` (1024px), `xl:` (1280px)
- `useState<boolean>` for sidebar open state in ChatShell
- CSS transitions for drawer animation (`transition-transform`)

### Component Patterns
- All components: TypeScript with strict types
- Props interfaces defined inline (no external types file unless shared)
- CSS-only implementations (no external animation libraries)
- Cosmic glow effects: `shadow-[0_0_Npx_rgba(R,G,B,A)]` Tailwind arbitrary values

### Performance
- Streaming UX: existing pattern preserved (no changes to SSE logic)
- CompCard: memo with `React.memo` for expensive rerenders
- CitationCard: virtualization not needed (typically <10 citations)

---

*UI-SPEC.md generated from discuss-phase decisions — all design decisions locked in 12-CONTEXT.md*
