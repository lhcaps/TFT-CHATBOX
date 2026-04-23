"""Centralized JSON loading utilities for graph construction."""
import json
from pathlib import Path


def get_project_root() -> Path:
    """Return the project root directory (parent of apps/)."""
    # Path: .../Tft Chatbox/apps/backend/app/graph/loader.py
    # parents[4]: .../Tft Chatbox
    return Path(__file__).resolve().parents[4]


def load_json(filename: str) -> dict:
    """Load a JSON file from the project root.
    
    Args:
        filename: Name of JSON file (e.g., "tft_set17_patch17_1_data_pack.json")
    Returns:
        Parsed JSON dict
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    root = get_project_root()
    file_path = root / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)
