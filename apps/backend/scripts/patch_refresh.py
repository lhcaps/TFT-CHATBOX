#!/usr/bin/env python3
"""Refresh TFT patch data from cached sources."""
from __future__ import annotations

import json
from pathlib import Path

TFT_PATCH_CACHE = Path.home() / ".tft-copilot" / "patch_cache.json"


def load_latest_patch() -> dict:
    """Load the most recent patch data from local cache."""
    if not TFT_PATCH_CACHE.exists():
        return {}
    return json.loads(TFT_PATCH_CACHE.read_text(encoding="utf-8"))


def check_patch_update(previous: dict, current: dict) -> list[str]:
    """Compare two patch versions and return changed keys."""
    changes = []
    for key in set(previous.keys()) | set(current.keys()):
        if previous.get(key) != current.get(key):
            changes.append(key)
    return changes


if __name__ == "__main__":
    patch = load_latest_patch()
    print(f"Loaded patch data: {patch.get('patch_version', 'unknown')}")
