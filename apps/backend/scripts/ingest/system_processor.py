"""SystemProcessor for tft_set17_patch17_1_data_pack.json — Space Gods + systems (RAG2-04)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .base_processor import BaseProcessor


class SystemProcessor(BaseProcessor):
    source_file = "tft_set17_patch17_1_data_pack.json"
    entity_type = "system"
    chunk_size = 350

    def get_data_path(self) -> Path:
        backend_dir = Path(__file__).parent.parent.parent.parent
        return backend_dir / self.source_file

    def load_data(self) -> list[dict]:
        """Load system entries: Space Gods + Realm of the Gods + patch changes."""
        data_path = self.get_data_path()
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        import json
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        systems = []

        # Realm of the Gods
        rotg = data.get("systems", {}).get("realm_of_the_gods", {})
        if rotg:
            flow = rotg.get("flow", [])
            systems.append({
                "type": "system",
                "name": "Realm of the Gods",
                "replaces": rotg.get("replaces", "Carousel"),
                "description": " ".join(flow) if flow else "",
            })

        # Space Gods
        for god in data.get("systems", {}).get("space_gods", []):
            systems.append({
                "type": "god",
                "name": god.get("name", ""),
                "title": god.get("title", ""),
                "focus": god.get("focus", ""),
            })

        # Patch 17.1B highlights
        highlights = data.get("systems", {}).get("patch_17_1b_highlights", {})
        if highlights:
            augments_removed = highlights.get("augments_removed", [])
            if augments_removed:
                systems.append({
                    "type": "patch_changes",
                    "name": "Patch 17.1B Changes",
                    "description": f"Augments removed: {', '.join(augments_removed)}",
                })

        return systems

    def process_item(self, item: dict) -> list[dict]:
        name = item.get("name", "")
        item_type = item.get("type", "system")
        title = item.get("title", "")
        focus = item.get("focus", "")
        description = item.get("description", "")
        replaces = item.get("replaces", "")

        content_parts = [f"## {name}"]
        if title:
            content_parts.append(f"**Title:** {title}")
        if replaces:
            content_parts.append(f"**Replaces:** {replaces}")
        if focus:
            content_parts.append(f"**Focus:** {focus}")
        if description:
            content_parts.append(description)

        content = "\n\n".join(content_parts)
        if len(content) > self.chunk_size:
            content = content[: self.chunk_size - 3] + "..."

        return [{
            "content": content,
            "source": self.source_file,
            "metadata": {
                "entity_type": self.entity_type,
                "system_name": name,
                "system_type": item_type,
                "patch": "17.1",
                "set": 17,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        }]
