---
phase: 12-ui-ux-redesign
plan: "02"
subsystem: frontend-ui
tags: [ui, citation, modal, source-filter]
key-files:
  created:
    - apps/frontend/src/components/CitationModal.tsx
  modified:
    - apps/frontend/src/components/CitationCard.tsx
    - apps/frontend/src/components/MessageList.tsx
metrics:
  files_created: 1
  files_modified: 2
  lines_added: ~180
  lines_removed: ~50

## Summary

Upgraded CitationCard to v2 with click-to-expand modal and source filtering. Created CitationModal with backdrop overlay, full citation text display, and clipboard copy button. Integrated source filter buttons (All/Obsidian/Patch/MetaTFT) into MessageList.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| CitationModal creation | 679771b | Fixed inset-0 z-50 modal with backdrop blur, copy + close buttons |
| CitationCard v2 rewrite | 679771b | 200-char truncation, cursor-pointer, onClick handler |
| MessageList integration | 679771b | selectedCitation state, sourceFilter state, filteredCitations, CitationModal rendered |

## What Was Built

- **CitationModal.tsx** (new): Full-screen modal overlay with `bg-black/60 backdrop-blur-sm`. Shows source, heading, percent match, full text, copy button (navigator.clipboard), close button. Click backdrop to close.
- **CitationCard.tsx** (rewritten): 200-char truncation with "..." + "Click to read more" hint. cursor-pointer hover effect. onClick prop for modal trigger. No more line-clamp-3.
- **MessageList.tsx** (updated): Added selectedCitation/useState, sourceFilter/useState, filteredCitations logic, source filter buttons (All/Obsidian/Patch/MetaTFT) with purple active state, CitationModal rendered at end of component.

## Deviations

None.

## Self-Check

- [x] CitationModal.tsx exists with bg-black/60 backdrop-blur-sm
- [x] CitationCard.tsx contains cursor-pointer, "Click to read more", onClick prop, truncatedText
- [x] MessageList.tsx contains CitationModal import, selectedCitation state, sourceFilter state, filteredCitations, CitationModal rendered at end
- [x] Source filter buttons use purple active state (bg-purple-600)
