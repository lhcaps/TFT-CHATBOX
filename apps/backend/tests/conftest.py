"""Shared fixtures for graph tests."""
from __future__ import annotations

import pytest
from pathlib import Path
from networkx import MultiDiGraph


# Path to project root (parent of apps/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def project_root():
    """Return the project root directory path."""
    return PROJECT_ROOT


@pytest.fixture
def mini_champions():
    """Mini champion list for fast tests."""
    return [
        {"name": "Briar", "cost": 3, "traits": [{"name": "Anima", "count": 1}]},
        {"name": "Jinx", "cost": 3, "traits": [{"name": "Anima", "count": 1}]},
        {"name": "Illaoi", "cost": 4, "traits": [{"name": "Anima", "count": 1}]},
    ]


@pytest.fixture
def mini_items():
    """Mini item list for fast tests."""
    return [
        {"name": "Bloodthirster", "recipe": ["B.F. Sword", "Negatron Cloak"]},
        {"name": "Bramble Vest", "recipe": ["Chain Vest", "Chain Vest"]},
    ]


@pytest.fixture
def mini_traits():
    """Mini trait list for fast tests."""
    return {
        "Anima": {
            "champions": ["Briar", "Jinx", "Illaoi"],
            "tiers": {"3": "Start Researching!"},
        }
    }


@pytest.fixture
def sample_graph():
    """Build a small graph from mini fixtures for fast unit tests."""
    G = MultiDiGraph()

    # Add trait node
    G.add_node("anima", type="trait", name="Anima", trait_type="origin",
               breakpoints=[3, 6], is_verified=True)

    # Add champion nodes + edges
    for champ in [
        {"name": "Briar", "cost": 3, "traits": [{"name": "Anima", "count": 1}]},
        {"name": "Jinx", "cost": 3, "traits": [{"name": "Anima", "count": 1}]},
    ]:
        champ_id = champ["name"].lower()
        G.add_node(champ_id, type="champion", name=champ["name"],
                   cost=champ["cost"], traits=champ["traits"], is_verified=True)
        G.add_edge(champ_id, "anima", edge_type="HAS_TRAIT", count=1)

    # Add item nodes + BUILDS_FROM edges
    G.add_node("b_f_sword", type="item", name="B.F. Sword",
                category="component", recipe=[], is_verified=True)
    G.add_node("negatron_cloak", type="item", name="Negatron Cloak",
                category="component", recipe=[], is_verified=True)
    G.add_node("bloodthirster", type="item", name="Bloodthirster",
                category="standard", recipe=["B.F. Sword", "Negatron Cloak"],
                is_verified=True)
    G.add_edge("bloodthirster", "b_f_sword", edge_type="BUILDS_FROM", role="component")
    G.add_edge("bloodthirster", "negatron_cloak", edge_type="BUILDS_FROM", role="component")

    # Add ITEM_FOR_CHAMPION edge
    G.add_edge("bloodthirster", "briar", edge_type="ITEM_FOR_CHAMPION",
               role="AD", confidence="heuristic")

    return G
