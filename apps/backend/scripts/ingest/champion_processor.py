"""ChampionProcessor for champions from tft_set17_patch17_1_data_pack.json (RAG2-04).

Note: deep_pack_v4_user_verified.json not present in project root.
Uses champions list from the unified data pack instead.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .base_processor import BaseProcessor


class ChampionProcessor(BaseProcessor):
    source_file = "tft_set17_patch17_1_data_pack.json"
    entity_type = "champion"
    chunk_size = 400

    def get_data_path(self) -> Path:
        backend_dir = Path(__file__).parent.parent.parent.parent
        return backend_dir / self.source_file

    def load_data(self) -> list[dict]:
        """Load champion list from data pack."""
        data_path = self.get_data_path()
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        import json
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("champions", [])

    def process_item(self, item: dict) -> list[dict]:
        name = item.get("name", "")
        cost = item.get("cost", 0)
        traits = item.get("traits", [])
        ability = item.get("ability", {})
        ability_name = ability.get("name", "") if isinstance(ability, dict) else ""
        ability_desc = ability.get("description", "") if isinstance(ability, dict) else ""

        traits_str = ", ".join(traits) if isinstance(traits, list) else str(traits)

        content = f"""## {name} (Cost {cost})

**Traits:** {traits_str}
**Ability:** {ability_name}
{ability_desc}
"""
        if len(content) > self.chunk_size:
            content = content[: self.chunk_size - 3] + "..."

        return [{
            "content": content,
            "source": self.source_file,
            "metadata": {
                "entity_type": self.entity_type,
                "champion_name": name,
                "cost": cost,
                "traits": traits if isinstance(traits, list) else [],
                "patch": "17.1",
                "set": 17,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        }]
