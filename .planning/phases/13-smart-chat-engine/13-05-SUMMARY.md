---
phase: "13-smart-chat-engine"
plan: "05"
subsystem: "frontend|backend"
tags: ["coach-mode", "line-of-play", "scenario-presets", "smart-chat"]
key-files:
  created:
    - "apps/frontend/src/components/CoachLineOfPlay.tsx"
  modified:
    - "apps/backend/app/prompts.py"
    - "apps/frontend/src/components/Composer.tsx"
    - "apps/frontend/src/components/ChatShell.tsx"
    - "apps/frontend/src/utils/compParser.ts"
    - "apps/frontend/src/components/MessageList.tsx"
metrics:
  coach_prompt_updated: true
  scenario_presets: 4
  coach_blocks_parsed: true
---

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Coach prompt updated with line-of-play format + scenario tag recognition | `91e1876` |
| 2 | CoachLineOfPlay: primary lines card with econ/items/timing/risk + pivot fallback | `91e1876` |
| 3 | Scenario preset chips in Composer (coach mode only), prepend tag to message | `91e1876` |
| 4 | parseCoachBlocks + hasCoachContent in compParser.ts, MessageContent detects coach content | `91e1876` |

## Deviations

- Coach prompt entity JSON markers section was already added in 13-01; extended with line-of-play + scenario sections
- CoachLineOfPlay wired into MessageList via hasCoachContent() detection (messageRole='assistant' check)
- No other deviations.

## Self-Check

- [x] Coach prompt: `grep "PIVOT FALLBACK" apps/backend/app/prompts.py` returns 1
- [x] CoachLineOfPlay: `grep "export function CoachLineOfPlay" apps/frontend/src/components/CoachLineOfPlay.tsx` returns 1
- [x] Scenario presets: `grep "SCENARIO_PRESETS" apps/frontend/src/components/Composer.tsx` returns 1
- [x] Coach parser: `grep "parseCoachBlocks" apps/frontend/src/utils/compParser.ts` returns 1
- [x] No modifications to shared orchestrator artifacts
