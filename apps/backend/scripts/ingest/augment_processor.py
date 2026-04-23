"""AugmentProcessor for augments_full_user_verified.json — 252 augments (RAG2-04)."""
from __future__ import annotations

from datetime import datetime, timezone

from .base_processor import BaseProcessor


class AugmentProcessor(BaseProcessor):
    source_file = "augments_full_user_verified.json"
    entity_type = "augment"
    chunk_size = 350  # ~200-500 chars per augment

    def process_item(self, item: dict) -> list[dict]:
        name = item.get("name", "")
        tier = item.get("tier", "Unknown")  # Silver, Gold, Prismatic
        description = item.get("description", "")
        relevant_round = item.get("relevant_round", "")

        content_parts = [f"## {name} ({tier} Augment)"]
        if relevant_round:
            content_parts.append(f"**Best for:** {relevant_round}")
        content_parts.append(description)
        content = "\n\n".join(content_parts)

        if len(content) > self.chunk_size:
            content = content[: self.chunk_size - 3] + "..."

        return [{
            "content": content,
            "source": self.source_file,
            "metadata": {
                "entity_type": self.entity_type,
                "augment_name": name,
                "tier": tier,
                "relevant_round": relevant_round,
                "patch": "17.1",
                "set": 17,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        }]
