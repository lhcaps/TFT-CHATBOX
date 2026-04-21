"""Markdown parsing utilities."""
from __future__ import annotations

import re
from typing import Iterator


def extract_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter from markdown if present."""
    pattern = r"^---\n(.*?)\n---\n(.*)$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        lines = match.group(1).splitlines()
        fm = {}
        for line in lines:
            if ":" in line:
                key, _, value = line.partition(":")
                fm[key.strip()] = value.strip()
        return fm, match.group(2)
    return {}, text


def split_into_chunks(text: str, chunk_size: int = 512, overlap: int = 50) -> Iterator[str]:
    """Split text into overlapping chunks of approximately chunk_size characters."""
    words = text.split()
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        yield chunk
        start += chunk_size - overlap
