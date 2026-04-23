"""RollingOddsProcessor for rolling odds data (RAG2-04)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .base_processor import BaseProcessor


_ROLLING_ODDS_FILE = "rolling_odds_user_verified.json"


class RollingOddsProcessor(BaseProcessor):
    source_file = _ROLLING_ODDS_FILE
    entity_type = "system"
    chunk_size = 200

    def get_data_path(self) -> Path:
        backend_dir = Path(__file__).parent.parent.parent.parent
        return backend_dir / self.source_file

    def load_data(self) -> list[dict]:
        """Load rolling odds data, or generate from embedded defaults if file missing."""
        try:
            return super().load_data()
        except FileNotFoundError:
            # Provide embedded rolling odds for Set 17 Patch 17.1
            return [
                {"level": 3, "odds": {"1-cost": "100%", "2-cost": "0%", "3-cost": "0%", "4-cost": "0%", "5-cost": "0%"}},
                {"level": 4, "odds": {"1-cost": "75%", "2-cost": "25%", "3-cost": "0%", "4-cost": "0%", "5-cost": "0%"}},
                {"level": 5, "odds": {"1-cost": "55%", "2-cost": "30%", "3-cost": "15%", "4-cost": "0%", "5-cost": "0%"}},
                {"level": 6, "odds": {"1-cost": "45%", "2-cost": "33%", "3-cost": "20%", "4-cost": "2%", "5-cost": "0%"}},
                {"level": 7, "odds": {"1-cost": "25%", "2-cost": "35%", "3-cost": "30%", "4-cost": "10%", "5-cost": "0%"}},
                {"level": 8, "odds": {"1-cost": "19%", "2-cost": "30%", "3-cost": "35%", "4-cost": "15%", "5-cost": "1%"}},
                {"level": 9, "odds": {"1-cost": "10%", "2-cost": "20%", "3-cost": "35%", "4-cost": "30%", "5-cost": "5%"}},
            ]

    def process_item(self, item: dict) -> list[dict]:
        level = item.get("level", item.get("dvo_level", ""))
        odds = item.get("odds", item.get("rolling_odds", {}))

        content_parts = [f"## Rolling Odds — Level {level}"]

        if isinstance(odds, dict):
            for cost, percentage in odds.items():
                content_parts.append(f"- **{cost}:** {percentage}")
        elif isinstance(odds, list):
            for odd in odds:
                if isinstance(odd, dict):
                    cost = odd.get("cost", odd.get("champion_cost", "?"))
                    pct = odd.get("odds", odd.get("percentage", "?"))
                    content_parts.append(f"- **{cost}-cost:** {pct}%")

        content = "\n".join(content_parts)
        if len(content) > self.chunk_size:
            content = content[: self.chunk_size - 3] + "..."

        return [{
            "content": content,
            "source": self.source_file,
            "metadata": {
                "entity_type": self.entity_type,
                "system": "rolling_odds",
                "level": level,
                "patch": "17.1",
                "set": 17,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        }]
