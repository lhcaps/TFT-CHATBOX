"""ItemProcessor for items_effects_expanded_set17.json — 45+ items (RAG2-04).

Falls back to extracting items from tft_set17_patch17_1_data_pack.json if the dedicated file is missing.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .base_processor import BaseProcessor


_ITEM_PACKS = [
    "items_effects_expanded_set17.json",
    "items_set17.json",
]


class ItemProcessor(BaseProcessor):
    source_file = "items_effects_expanded_set17.json"  # Primary — fallback handled in load_data
    entity_type = "item"
    chunk_size = 300

    def get_data_path(self) -> Path:
        backend_dir = Path(__file__).parent.parent.parent.parent
        # Try primary path first
        primary = backend_dir / self.source_file
        if primary.exists():
            return primary
        # Fallback: try alternate names
        for name in _ITEM_PACKS:
            if name != self.source_file:
                alt = backend_dir / name
                if alt.exists():
                    return alt
        return primary  # Will fail with FileNotFoundError at load time

    def process_item(self, item: dict) -> list[dict]:
        name = item.get("name", "")
        category = item.get("category", "Unknown")
        stats = item.get("stats", [])
        effect = item.get("effect", item.get("description", ""))
        recipe = item.get("recipe", [])

        content_parts = [f"## {name} ({category} Item)"]
        if recipe:
            content_parts.append(f"**Recipe:** {' + '.join(recipe)}")
        if stats:
            stats_str = ', '.join(stats) if isinstance(stats, list) else str(stats)
            content_parts.append(f"**Stats:** {stats_str}")
        if effect:
            content_parts.append(f"**Effect:** {effect}")

        content = "\n\n".join(content_parts)
        if len(content) > self.chunk_size:
            content = content[: self.chunk_size - 3] + "..."

        return [{
            "content": content,
            "source": self.source_file,
            "metadata": {
                "entity_type": self.entity_type,
                "item_name": name,
                "category": category,
                "patch": "17.1",
                "set": 17,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        }]
