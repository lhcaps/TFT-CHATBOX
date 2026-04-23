"""Heuristic ITEM_FOR_CHAMPION edge assignment for the knowledge graph."""
from __future__ import annotations

import re
from typing import Any

import networkx as nx


# Trait → primary role mapping
TRAIT_ROLE_MAP: dict[str, str] = {
    "anima": "AP",       # Anima = HP/sustain but champions are casters (Briar, Jinx)
    "primordian": "TANK", # HP / Swarmlings
    "vanguard": "TANK",  # Armor / frontline
    "bastion": "TANK",   # Armor / MR / frontline
    "invoker": "AP",     # Spellcasting
    "conduit": "AP",     # Spellcasting / mana
    "rogue": "AD",       # Physical damage
    "marauder": "AD",    # AD / Omnivamp
    "sniper": "AD",     # Ranged AD
    "challenger": "AD",  # Attack speed / AD
}


def normalize_item_id(name: str) -> str:
    """Normalize item/component name to graph node ID."""
    return re.sub(r'[^a-z0-9]+', '_', name.lower().strip()).strip('_')


def infer_role(cost: int, traits: list) -> str:
    """Infer champion role from traits first, then cost.
    
    Trait-based inference takes priority over cost-based inference.
    """
    trait_names = [t.lower() for t in traits]
    for trait in trait_names:
        if trait in TRAIT_ROLE_MAP:
            return TRAIT_ROLE_MAP[trait]
    if cost >= 4:
        return "AD"
    return "TANK"


def categorize_item(recipe: list[str]) -> str:
    """Categorize item by its components.
    
    Categories:
      - AD:     B.F. Sword or Recurve Bow (no AP components)
      - AP:     Needlessly Large Rod or Tear of the Goddess
      - TANK:   Chain Vest, Giant's Belt, or Negatron Cloak (mostly defensive)
      - SUPPORT: mixed or unknown
    """
    AD_COMPONENTS = {"b_f_sword", "recurve_bow"}
    AP_COMPONENTS = {"needlessly_large_rod", "tear_of_the_goddess", "sparring_gloves"}
    TANK_COMPONENTS = {"chain_vest", "giants_belt", "negatron_cloak"}

    normalized_recipe = {normalize_item_id(r) for r in recipe}

    if normalized_recipe & AD_COMPONENTS and not (normalized_recipe & AP_COMPONENTS):
        return "AD"
    if normalized_recipe & AP_COMPONENTS:
        return "AP"
    if normalized_recipe & TANK_COMPONENTS and len(normalized_recipe - TANK_COMPONENTS) <= 1:
        return "TANK"
    return "SUPPORT"


def assign_item_edges(G: nx.MultiDiGraph, champions: list[dict], items: list[dict]) -> None:
    """Assign ITEM_FOR_CHAMPION edges based on inferred role.
    
    For each champion, assign top 3 items matching their role.
    Skips champions/items not in the graph.
    """
    # Build item index by category
    items_by_role: dict[str, list[str]] = {"AD": [], "AP": [], "TANK": [], "SUPPORT": []}
    for item in items:
        name = item.get("name", "")
        if not name:
            continue
        iid = normalize_item_id(name)
        if iid not in G:
            continue
        role = categorize_item(item.get("recipe", []))
        items_by_role[role].append(iid)

    # Assign to champions
    for champ in champions:
        name = champ.get("name", "")
        if not name:
            continue
        champ_id = normalize_item_id(name)
        if champ_id not in G:
            continue
        role = infer_role(champ.get("cost", 3), champ.get("traits", []))
        for iid in items_by_role.get(role, [])[:3]:
            G.add_edge(
                iid, champ_id,
                edge_type="ITEM_FOR_CHAMPION",
                role=role,
                confidence="heuristic",
            )
