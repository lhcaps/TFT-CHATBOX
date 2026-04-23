# Phase 12: UI/UX Core Redesign - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 12-ui-ux-redesign
**Areas discussed:** Layout/Overflow, CitationCard Expand, CompCard Migration, Responsive Breakpoints, Empty State

---

## Area 1: Layout & Overflow

|| Option | Description | Selected |
|--------|---------|----------|
| Smart (70%/90%/100%) | 70% desktop, 90% tablet, 100% mobile | ✅ |
| Simple (100% mobile) | Full width for readability on all screen sizes | |

**User's choice:** Smart (70%/90%/100%)
**Notes:** Desktop stays at 70%, tablet gets 90%, mobile gets full 100% width.

---

## Area 2: CitationCard Expand

### 2a: Expand Behavior

|| Option | Description | Selected |
|--------|---------|----------|
| Click to expand | Truncate with line-clamp-3, click to see more | ✅ |
| Full text | Always show full text, no truncation | |

**User's choice:** Click to expand

### 2b: Expand Implementation

|| Option | Description | Selected |
|--------|---------|----------|
| Inline expand | Card grows in-place vertically | |
| Modal | Full-screen or centered dialog overlay | ✅ |

**User's choice:** Modal

---

## Area 3: CompCard Migration

### 3a: Migration Strategy

|| Option | Description | Selected |
|--------|---------|----------|
| Migrate to Tailwind | Full Tailwind migration, custom styled divs | ✅ |
| Hybrid | Keep color constants, add responsive Tailwind | |

**User's choice:** Migrate to Tailwind + shadcn/ui for a "bóng bẩy" (glossy, polished) look that fits the Set 17 theme.

### 3b: shadcn/ui Integration

|| Option | Description | Selected |
|--------|---------|----------|
| Use shadcn Card | Use shadcn Card component, keep existing layout | |
| Custom styled divs | Custom divs with Tailwind classes, fully customizable | ✅ |

**User's choice:** Custom styled divs — user wants full customization for cosmic Space Gods theme.

---

## Area 4: Responsive Breakpoints

### 4a: Mobile Navigation

|| Option | Description | Selected |
|--------|---------|----------|
| Sidebar → Drawer | Slide-in drawer on mobile, hamburger menu toggle | ✅ |
| Tab-based | Tabs instead of sidebar on mobile | |

**User's choice:** Drawer (slide-in)

### 4b: Header Layout

|| Option | Description | Selected |
|--------|---------|----------|
| Responsive flex/gap | Replace fixed w-64, use flexbox layout | ✅ |
| Compact tabs | Keep w-64 but shrink font/padding | |

**User's choice:** Responsive flex/gap — cleaner and more modern.

---

## Area 5: Empty State / Welcome Screen

### 5a: Design Direction

|| Option | Description | Selected |
|--------|---------|----------|
| TFT-themed | Add Set 17 Space Gods theming | ✅ |
| Minimal | Keep simple text, no visuals | |

**User's choice:** TFT-themed (Space Gods theme)

### 5b: Theme Detail

|| Option | Description | Selected |
|--------|---------|----------|
| Cosmic/galaxy | Gradient background + constellation SVG icons | ✅ |
| Simple cosmic | Cosmic gradient + space icon | |

**User's choice:** Cosmic/galaxy — constellation SVG icons + gradient background

---

## Summary

**Total areas discussed:** 6 (5 main + 1 follow-up)
**Corrections made:** 0 (all options confirmed by user)
**Deferred ideas:** Phase 13 entity cards, Phase 14 streaming citations

---

*Discussion log: 2026-04-23*
