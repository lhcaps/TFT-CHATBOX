# Phase 12: UI/UX Core Redesign - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix layout overflow bugs and create a polished, responsive chat interface for TFT Local Copilot. Fix message bubble overflow, upgrade CitationCard to v2 with modal expand, migrate CompCard to Tailwind + custom styled components with Set 17 Space Gods theme, add responsive breakpoints with sidebar drawer, and create a cosmic-themed empty state.

**Scope:**
- Layout refactor: overflow fix, min-w-0, max-w enforcement, scroll isolation
- CitationCard v2: expandable, collapsible, modal expand, source filter
- CompCard Tailwind migration: custom styled divs (not shadcn Card), Set 17 Space Gods cosmic theme
- Responsive breakpoints: mobile sidebar drawer, flex/gap header layout
- Loading states + streaming UX polish: cosmic-themed welcome screen

**Out of scope:** Phase 13 entity cards (ChampionProfile, ItemCard, etc.), Phase 14 streaming citations

</domain>

<decisions>
## Implementation Decisions

### Layout & Overflow (D-01)
- **Message bubble width:** Smart responsive breakpoints
  - Desktop (≥1024px): `max-w-[70%]`
  - Tablet (768-1024px): `max-w-[90%]`
  - Mobile (<768px): `max-w-full` (100% width for readability)
- **Container overflow:** Add `min-w-0` to MessageList flex container and `overflow-x-hidden` on parent
- **Word wrap:** `overflow-wrap: break-word` on message bubbles for long URLs and code blocks
- **CitationCard truncation:** Remove `line-clamp-3` in favor of modal expand

### CitationCard v2 (D-02)
- **Expand behavior:** Click opens a modal overlay (full-screen or centered dialog) showing full citation text
- **Collapsible sections:** Card shows source + heading by default; click expands to show full text in modal
- **Source filter:** Dropdown or toggle to filter citations by source type (Obsidian, patch notes, metatft)
- **Copy button:** Copy citation text to clipboard
- **Use existing:** `~/components/ui/card` (shadcn Card) for base structure
- **NOT inline expand:** Modal chosen over inline height expansion

### CompCard Tailwind Migration (D-03)
- **Migration approach:** Full Tailwind migration using custom styled divs
- **Style system:** Tailwind utility classes throughout — NO inline styles
- **Theme:** Set 17 Space Gods cosmic/galaxy theme
  - Dark cosmic background gradients (deep purple → dark blue)
  - Glowing border effects using Tailwind ring/ring-offset utilities
  - Tier colors: S=Gold (#fbbf24), A=Silver (#9ca3af), B=Bronze (#b45309)
  - Item type colors: AD=Red, AP=Blue, Tank=Green, Support=Purple
  - Font: existing Tailwind default (Inter/system-ui)
- **Components:** Custom divs with Tailwind classes (NOT shadcn Card — too constrained for the cosmic design)
- **Color constants:** Keep AD_ITEMS, AP_ITEMS, TANK_ITEMS, SUPPORT_ITEMS, TIER_COLORS as JS Sets/objects (already exist)
- **Responsive:** Ensure CompCard doesn't overflow on tablet/mobile

### Responsive Breakpoints (D-04)
- **Sidebar → Drawer:**
  - Desktop (≥1024px): Sidebar 256px (`w-64`) fixed on left
  - Tablet (768-1024px): Sidebar collapsible panel (toggle button)
  - Mobile (<768px): Sidebar becomes slide-in drawer (hamburger menu button)
- **Implementation:** React state for `sidebarOpen`, Tailwind conditional classes
  - Mobile: `fixed inset-0 z-50` drawer with backdrop overlay
  - Drawer: slide from left with `transform -translate-x-full` transition
- **Header layout:** Replace `w-64` fixed ModeTabs with responsive flex/gap layout
  - Use `flex items-center gap-2` instead of fixed width
  - Mode tabs scale gracefully across breakpoints

### Empty State / Welcome Screen (D-05)
- **Design:** Cosmic/galaxy themed empty state
- **Visual elements:**
  - Gradient background: deep purple (#0f0c29) → dark blue (#302b63) → purple (#24243e)
  - SVG constellation-style icon (stars, cosmic pattern)
  - Space Gods theme: subtle glow effects, cosmic color palette
- **Content:** Keep existing text but style with cosmic typography
  - "Ask about TFT strategies, comps, augments, or patch notes."
  - "Switch modes above to search notes or get coaching."
- **Implementation:** Custom div with Tailwind bg-gradient, SVG inline icon, CSS glow effects

### the agent's Discretion
- Exact CSS gradient values for cosmic background (may refine during implementation)
- Exact drawer transition duration (default: 300ms)
- Exact modal size for CitationCard expand (full-screen vs centered dialog)
- Whether to use shadcn Dialog for CitationCard modal or custom implementation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/ROADMAP.md` — Phase 12 goal, scope, 5 plans (UI-01..UI-05), traceability
- `.planning/STATE.md` — current project state, Phase 11 complete, v1.4 in progress
- `.planning/PROJECT.md` — project vision, stack summary, constraints
- `.planning/REQUIREMENTS.md` — UI-01..UI-05 acceptance criteria

### Frontend Codebase
- `apps/frontend/src/components/ChatShell.tsx` — Main layout, sidebar, header (read first)
- `apps/frontend/src/components/MessageList.tsx` — Message bubbles, overflow context
- `apps/frontend/src/components/CitationCard.tsx` — Current CitationCard to upgrade
- `apps/frontend/src/components/Composer.tsx` — Input component, auto-grow pattern
- `apps/frontend/src/components/ModeTabs.tsx` — Mode toggle tabs
- `apps/frontend/src/components/CompCard.tsx` — Current CompCard with inline styles (295 lines)
- `apps/frontend/src/utils/compParser.ts` — `parseCompCard()` and `parseCompBlocks()`
- `apps/frontend/src/api/types.ts` — Message, Citation types
- `apps/frontend/src/components/ui/card.tsx` — shadcn Card component
- `apps/frontend/src/components/ui/button.tsx` — shadcn Button component
- `apps/frontend/src/hooks/useToast.ts` — Existing toast pattern (CSS-only, no dependency)
- `apps/frontend/tsconfig.json` — TypeScript config, path alias `~/`
- `apps/frontend/vite.config.ts` — Vite config with proxy to backend

### Prior Phase Context
- `.planning/phases/03-frontend-chat/03-CONTEXT.md` — Frontend architecture decisions (React 18, Vite 6, Tailwind v4, SSE, no routing library, hooks state management)
- `.planning/phases/10-hardening-polish/10-CONTEXT.md` — CompCard exists, toast pattern, session switch loading

### Set 17 Data Files (for cosmic theme)
- `tft_set17_patch17_1_enhanced_pack.json` — Space Gods data for cosmic theme inspiration
- `augments_full_user_verified.json` — 252 augments for content reference

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `~/components/ui/card` (shadcn Card) — can reuse for CitationCard v2 base structure
- `~/components/ui/button` (shadcn Button) — for drawer toggle, modal close
- `compParser.ts` — `parseCompCard()` and `parseCompBlocks()` already exist, no changes needed
- Toast pattern (`useToast.ts`) — CSS-only implementation, no external deps

### Established Patterns
- Tailwind v4 via `@tailwindcss/vite` — no tailwind.config.js (v4 uses CSS config)
- Dark theme: `bg-gray-900`, `text-white`, `border-gray-700` throughout
- Cosmic theme should follow existing dark palette but with purple/blue accents
- Vite proxy: `/api/*` → `http://localhost:8000/api`
- All components: TypeScript strict types

### Integration Points
- `ChatShell.tsx` line 50: root `<div className="flex h-screen bg-gray-900 text-white overflow-hidden">`
  - Sidebar: line 52, `<aside className="w-64 shrink-0 ...">`
  - Main: line 93, `<div className="flex-1 flex flex-col min-w-0">` (already has min-w-0 ✅)
- `MessageList.tsx` line 20: `<div className="flex-1 overflow-y-auto space-y-4 p-6">` — needs overflow-x-hidden
- `MessageList.tsx` line 38: `<div className={`max-w-[70%] rounded-2xl...`}>` — needs responsive variants
- `Composer.tsx` line 40: `<div className="border-t border-gray-700 bg-gray-800 px-6 py-4">` — needs mobile padding
- `CompCard.tsx` lines 1-294: entire file needs rewrite — all inline styles to Tailwind

</code_context>

<specifics>
## Specific Ideas

### Cosmic Theme Colors (Space Gods Set 17)
```
Background gradient: from-[#0f0c29] via-[#302b63] to-[#24243e]
Tier S: text-yellow-400 / border-yellow-500
Tier A: text-gray-300 / border-gray-400
Tier B: text-orange-400 / border-orange-600
Glow effect: shadow-[0_0_15px_rgba(139,92,246,0.3)] (purple glow)
```

### CompCard Tailwind Structure
```tsx
// Header with cosmic gradient border
<div className="rounded-xl border border-purple-500/50 bg-linear-to-br from-purple-900/20 to-blue-900/20">
  {/* Tier badge with glow */}
  <span className="text-yellow-400 font-bold shadow-[0_0_8px_rgba(251,191,36,0.4)]">S</span>
  {/* Stats, items, units, traits with Tailwind spacing */}
</div>
```

### CitationCard Modal
```tsx
// Modal overlay using existing patterns from toast.tsx (CSS-only)
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
  <div className="bg-gray-800 rounded-2xl border border-gray-600 p-6 max-w-2xl w-full mx-4">
    {/* Full citation text */}
  </div>
</div>
```

### Responsive Drawer
```tsx
// Mobile only: fixed drawer
{isMobile && sidebarOpen && (
  <div className="fixed inset-0 z-50">
    <div className="absolute inset-0 bg-black/50" onClick={closeSidebar} />
    <aside className="absolute left-0 top-0 h-full w-64 bg-gray-800 transform transition-transform">
      {/* Sidebar content */}
    </aside>
  </div>
)}
```

</specifics>

<deferred>
## Deferred Ideas

### Future Phase Candidates
- **Phase 13 (Smart Chat Engine)** — ChampionProfile, ItemCard, TraitCard, AugmentCard inline components (new entity cards, separate from CitationCard v2)
- **Phase 13 (Smart Chat Engine)** — Smart reply suggestions (context-aware chips)
- **Phase 14 (RAG 2.0)** — Streaming citations (citation_start/citation_end SSE events)

### Out of Scope for Phase 12
- Entity JSON markers parsing (Phase 13)
- Smart routing based on query type (Phase 13)
- Cross-entity query patterns (Phase 13)
- RAG 2.0 metadata filtering (Phase 14)
- Obsidian file watcher (Phase 14)

</deferred>

---

*Phase: 12-ui-ux-redesign*
*Context gathered: 2026-04-23*
