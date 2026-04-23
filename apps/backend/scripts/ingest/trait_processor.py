"""TraitProcessor for traits — extracts origins + classes from data pack (RAG2-04)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .base_processor import BaseProcessor


class TraitProcessor(BaseProcessor):
    source_file = "tft_set17_patch17_1_data_pack.json"
    entity_type = "trait"
    chunk_size = 300

    def get_data_path(self) -> Path:
        backend_dir = Path(__file__).parent.parent.parent.parent
        return backend_dir / self.source_file

    def load_data(self) -> list[dict]:
        """Load traits (origins + classes) from the unified data pack."""
        data_path = self.get_data_path()
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        import json
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        traits = []
        # Origins
        for origin in data.get("origins", []):
            traits.append({
                "type": "origin",
                "name": origin.get("name", ""),
                "breakpoints": origin.get("breakpoints", []),
                "champions": origin.get("champions", []),
                "summary": origin.get("summary", ""),
            })
        # Classes
        for cls in data.get("classes", []):
            traits.append({
                "type": "class",
                "name": cls.get("name", ""),
                "breakpoints": cls.get("breakpoints", []),
                "champions": cls.get("champions", []),
                "summary": cls.get("summary", ""),
            })
        return traits

    def process_item(self, item: dict) -> list[dict]:
        name = item.get("name", "")
        trait_type = item.get("type", "trait")
        breakpoints = item.get("breakpoints", [])
        champions = item.get("champions", [])
        summary = item.get("summary", "")

        content_parts = [f"## {name} ({trait_type.title()})"]

        if breakpoints:
            bp_str = ", ".join(str(b) for b in breakpoints)
            content_parts.append(f"**Breakpoints:** {bp_str} units")

        if summary:
            content_parts.append(summary)

        if champions:
            champ_list = ", ".join(champions[:15])
            if len(champions) > 15:
                champ_list += f" (+{len(champions) - 15} more)"
            content_parts.append(f"**Champions:** {champ_list}")

        content = "\n\n".join(content_parts)
        if len(content) > self.chunk_size:
            content = content[: self.chunk_size - 3] + "..."

        return [{
            "content": content,
            "source": self.source_file,
            "metadata": {
                "entity_type": self.entity_type,
                "trait_name": name,
                "trait_type": trait_type,
                "champions": champions[:20],
                "patch": "17.1",
                "set": 17,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        }]
