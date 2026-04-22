#!/usr/bin/env python3
"""
Smoke test for TFT Local Copilot v1.2.
Tests 25 questions across 5 TFT categories (5 each):
  - comp:      team composition strategy
  - item:      item slam/build advice
  - augment:   augment tier and selection
  - pivot:     pivot decision between two options
  - meta:      MetaTFT real-time meta comps (Phase 9)

Each question is tested in all 3 modes (Normal, RAG, Coach) = 75 total calls.
A question PASSES if:
  - HTTP 200 response
  - No Python exception raised
  - Response body has > 10 non-whitespace characters

GPU memory is checked before and after via /api/health/gpu.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import httpx

# ─── Configuration ───────────────────────────────────────────────────────────────

BACKEND_BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{BACKEND_BASE}/api/chat"
GPU_ENDPOINT = f"{BACKEND_BASE}/api/health/gpu"
REQUEST_TIMEOUT = 120.0  # seconds — generous for LLM response

# Results file in the same directory as this script
SCRIPT_DIR = Path(__file__).parent
RESULTS_FILE = SCRIPT_DIR / "smoke_test_results.json"


# ─── Data types ────────────────────────────────────────────────────────────────

@dataclass
class Question:
    id: int
    category: str
    text: str


@dataclass
class QuestionResult:
    question: Question
    mode: str
    status_code: int | None
    passed: bool
    error: str | None
    response_length: int
    response_preview: str


@dataclass
class SmokeTestResult:
    results: list[QuestionResult] = field(default_factory=list)
    gpu_before: dict | None = None
    gpu_after: dict | None = None
    started_at: float = field(default_factory=time.time)


# ─── Test questions ─────────────────────────────────────────────────────────────

QUESTIONS: list[Question] = [
    # --- Comp (5) — Set 17 Space Gods ---
    Question(1, "comp", "What are the strongest S-tier comps in patch 17.1? Give me the top 3 with their carries."),
    Question(2, "comp", "Is Turbo Doomer (Vex/Bard/Rammus) a viable comp in the current meta?"),
    Question(3, "comp", "Which champions work best as a solo tank in Set 17 Space Gods?"),
    Question(4, "comp", "What is the best way to play Stay Groovy comp (Nami/Ornn) in patch 17.1?"),
    Question(5, "comp", "How do I itemize a board around Viktor carry in Set 17?"),

    # --- Item (5) — Set 17 patch 17.1B ---
    Question(6, "item", "Patch 17.1B nerfed tank items — is Warmog's still worth slamming early?"),
    Question(7, "item", "Which items are best for Viktor carry in Set 17?"),
    Question(8, "item", "I got Sparring Gloves on carousel — what are the best slamable items now?"),
    Question(9, "item", "How do I itemize a multi-carrier board with both a frontliner and backliner?"),
    Question(10, "item", "Rabadon's Deathcap got buffed to 55 AP in 17.1B — which AP carries benefit most?"),

    # --- Augment (5) — Set 17 augment pool ---
    Question(11, "augment", "Best first augment for a fast 8 roll down strategy?"),
    Question(12, "augment", "What augment tier should I prioritie when offered Portable Forge?"),
    Question(13, "augment", "Patch 17.1B removed Golden Dragon, Just Hit, Max Build — what replaces them?"),
    Question(14, "augment", "I hit a bad shop at 2-1 — how do I adapt my augment choices?"),
    Question(15, "augment", "Which silver augments are secretly S-tier in patch 17.1?"),

    # --- Pivot (5) — Set 17 champions & traits ---
    Question(16, "pivot", "I got 2-star Yone and 2-star Mordekaiser — which should I commit to?"),
    Question(17, "pivot", "I was playing Anima but hit 3 copies of Illaoi early. Should I pivot to Space Groove?"),
    Question(18, "pivot", "When should I abandon a pre-level-8 reroll comp and fast 9 instead?"),
    Question(19, "pivot", "My board is mid. Do I roll at 50 gold or push levels?"),
    Question(20, "pivot", "I hit an early 2-star 4-cost Viktor. Should I grief my 3-cost reroll plan?"),

    # --- Meta (5) — Phase 9: MetaTFT Real-time Intelligence ---
    Question(21, "meta", "What's the current S-tier comps from MetaTFT? Show me with CompCard format."),
    Question(22, "meta", "Which meta comp has the highest Top 4 rate right now? What's the best carry for it?"),
    Question(23, "meta", "Is there any hidden gem comp with high winrate that most players overlook?"),
    Question(24, "meta", "Compare the top 3 meta comps for patch 17.1 — which one is most flexible?"),
    Question(25, "meta", "What are the best slamable items for the current MetaTFT top comps?"),
]

MODES: list[Literal["normal", "rag", "coach"]] = ["normal", "rag", "coach"]
# Phase 9: meta mode is tested the same way — the LLM uses MetaTFT chunks in RAG/coach


# ─── Helpers ───────────────────────────────────────────────────────────────────

async def get_gpu_status(client: httpx.AsyncClient) -> dict:
    """Fetch GPU status from /api/health/gpu."""
    try:
        resp = await client.get(GPU_ENDPOINT, timeout=10.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


async def run_question(
    client: httpx.AsyncClient,
    question: Question,
    mode: str,
) -> QuestionResult:
    """Ask one question in one mode. Returns a result."""
    payload = {
        "message": question.text,
        "mode": mode,
        "session_id": f"smoke-test-q{question.id}-{mode}",
        "stream": False,
    }
    start = time.time()
    try:
        resp = await client.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        latency_ms = round((time.time() - start) * 1000)
        status = resp.status_code
        if status == 200:
            try:
                body = resp.json()
                text = body.get("text", "")
                preview = text[:80].replace("\n", " ")
                response_length = len(text.replace(" ", ""))
                passed = response_length > 10
                error = None
            except Exception as e:
                passed = False
                error = f"JSON parse error: {e}"
                response_length = 0
                preview = resp.text[:80].replace("\n", " ")
        else:
            passed = False
            error = f"HTTP {status}"
            response_length = 0
            preview = resp.text[:80].replace("\n", " ")
    except httpx.TimeoutException:
        passed = False
        error = "Timeout"
        response_length = 0
        preview = ""
        status = None
    except Exception as e:
        passed = False
        error = str(e)
        response_length = 0
        preview = ""
        status = None

    return QuestionResult(
        question=question,
        mode=mode,
        status_code=status,
        passed=passed,
        error=error,
        response_length=response_length,
        response_preview=preview,
    )


def print_summary(result: SmokeTestResult) -> None:
    """Print a formatted summary table."""
    elapsed = time.time() - result.started_at
    total = len(result.results)
    passed_count = sum(1 for r in result.results if r.passed)
    failed = [r for r in result.results if not r.passed]

    print()
    print("=" * 80)
    print("  SMOKE TEST SUMMARY")
    print("=" * 80)
    print(f"  Backend:  {BACKEND_BASE}")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  Result:   {passed_count}/{total} passed")
    print()

    # GPU summary
    gpu_b = result.gpu_before or {}
    gpu_a = result.gpu_after or {}
    if gpu_b.get("gpu_available") or gpu_a.get("gpu_available"):
        print(f"  GPU before: {gpu_b.get('vram_used_mb', 'N/A')} / {gpu_b.get('vram_total_mb', 'N/A')} MB")
        print(f"  GPU after:  {gpu_a.get('vram_used_mb', 'N/A')} / {gpu_a.get('vram_total_mb', 'N/A')} MB")
    else:
        print("  GPU status: unavailable")
    print()

    # Per-question summary (grouped by category + mode)
    print(f"  {'Q#':<4} {'Category':<10} {'Mode':<8} {'Result':<7} {'Response (chars)':<20} {'Preview'}")
    print("  " + "-" * 74)
    for r in result.results:
        marker = "PASS" if r.passed else "FAIL"
        char_count = f"{r.response_length} chars"
        preview = r.response_preview[:30]
        print(
            f"  {r.question.id:<4} {r.question.category:<10} {r.mode:<8} "
            f"{marker:<5} {char_count:<20} {preview}"
        )
    print()

    if failed:
        print(f"  FAILURES ({len(failed)}):")
        for r in failed:
            reason = r.error or "Empty response"
            print(f"    Q{r.question.id} [{r.question.category}] {r.mode}: {reason}")
        print()

    print("=" * 80)
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main() -> int:
    print("TFT Copilot Smoke Test v1.2")
    print(f"Backend: {BACKEND_BASE}")
    print(f"Questions: {len(QUESTIONS)} x {len(MODES)} modes = {len(QUESTIONS) * len(MODES)} calls")
    print()

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        # Fetch GPU status before
        gpu_before = await get_gpu_status(client)
        if gpu_before.get("gpu_available"):
            print(
                f"GPU before: {gpu_before.get('vram_used_mb')} / "
                f"{gpu_before.get('vram_total_mb')} MB "
                f"({gpu_before.get('percent_used')}%)"
            )

        result = SmokeTestResult(gpu_before=gpu_before)

        for i, question in enumerate(QUESTIONS):
            print(f"[{i+1:02d}/{len(QUESTIONS)}] Q{question.id} [{question.category}]: {question.text[:60]}...")
            for mode in MODES:
                r = await run_question(client, question, mode)
                result.results.append(r)
                marker = "PASS" if r.passed else "FAIL"
                detail = f"({r.error})" if not r.passed else ""
                print(f"    [{mode}] {marker} {detail} -- {r.response_length} chars")
            # Brief pause between questions to avoid overwhelming the LLM
            await asyncio.sleep(0.5)

        # Fetch GPU status after
        gpu_after = await get_gpu_status(client)
        result.gpu_after = gpu_after

    print_summary(result)

    # Print structured JSON for CI consumption
    summary = {
        "total": len(result.results),
        "passed": sum(1 for r in result.results if r.passed),
        "failed": sum(1 for r in result.results if not r.passed),
        "gpu_before": gpu_before,
        "gpu_after": gpu_after,
        "elapsed_seconds": round(time.time() - result.started_at, 1),
        "details": [
            {
                "question_id": r.question.id,
                "category": r.question.category,
                "mode": r.mode,
                "passed": r.passed,
                "error": r.error,
                "response_length": r.response_length,
            }
            for r in result.results
        ],
    }
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Detailed results saved to: {RESULTS_FILE}")

    # Exit code: 0 = all pass, 1 = any failure
    all_passed = all(r.passed for r in result.results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
