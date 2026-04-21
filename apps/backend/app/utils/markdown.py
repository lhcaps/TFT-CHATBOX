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


def split_into_chunks(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 500,
) -> Iterator[str]:
    """Split text into overlapping chunks of chunk_size characters.

    Tries to preserve paragraph boundaries, then sentence boundaries,
    then falls back to hard character splits.
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Split into paragraphs (blank line = paragraph break)
    paragraphs = re.split(r"\n\n+", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))

        # If not at end of text, try to break at boundary
        if end < len(text):
            # Try paragraph boundary first
            break_point = text.rfind("\n\n", start, end)
            if break_point > start:
                end = break_point + 2
            else:
                # Try sentence boundary (period, exclamation, question followed by space or newline)
                break_point = max(
                    text.rfind(". ", start, end),
                    text.rfind("! ", start, end),
                    text.rfind("? ", start, end),
                    text.rfind(".\n", start, end),
                    text.rfind("!\n", start, end),
                    text.rfind("?\n", start, end),
                )
                if break_point > start:
                    end = break_point + 2

        chunk = text[start:end].strip()
        if chunk:
            yield chunk

        # Move start back by overlap for next iteration
        start = end - overlap
        if start <= 0:
            start = end
