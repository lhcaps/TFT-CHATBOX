"""Modular batch processors for TFT data ingestion (RAG2-04)."""
from __future__ import annotations

from .base_processor import BaseProcessor
from .augment_processor import AugmentProcessor
from .champion_processor import ChampionProcessor
from .item_processor import ItemProcessor
from .trait_processor import TraitProcessor
from .system_processor import SystemProcessor
from .rolling_odds_processor import RollingOddsProcessor
from .data_pack_processor import DataPackProcessor

PROCESSOR_MAP: dict[str, type[BaseProcessor]] = {
    "augment": AugmentProcessor,
    "champion": ChampionProcessor,
    "item": ItemProcessor,
    "trait": TraitProcessor,
    "system": SystemProcessor,
    "rolling_odds": RollingOddsProcessor,
    "data_pack": DataPackProcessor,
}

__all__ = [
    "BaseProcessor",
    "AugmentProcessor",
    "ChampionProcessor",
    "ItemProcessor",
    "TraitProcessor",
    "SystemProcessor",
    "RollingOddsProcessor",
    "DataPackProcessor",
    "PROCESSOR_MAP",
]
