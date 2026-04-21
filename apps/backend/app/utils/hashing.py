"""Hashing utilities for content deduplication."""
from __future__ import annotations

import hashlib


def content_hash(text: str) -> str:
    """Compute a SHA-256 hash of the text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def short_hash(text: str, length: int = 16) -> str:
    """Compute a short hash of the text for use as an ID."""
    return content_hash(text)[:length]
