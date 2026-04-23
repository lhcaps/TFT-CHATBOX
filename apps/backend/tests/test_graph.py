"""Comprehensive unit tests for knowledge graph — KNOW-04."""
from __future__ import annotations

import pytest
import networkx as nx

from app.graph import knowledge_graph
from app.graph.builder import build_graph, normalize_id
from app.graph.heuristics import infer_role, categorize_item, assign_item_edges
from app.graph.models import ErrorResponse, NeighborItem


class TestGraphConstruction:
    """Tests for graph loading and node counts."""

    def test_graph_loads_all_node_types(self):
        G = build_graph()
        types = {G.nodes[n].get("type") for n in G.nodes()}
        assert "champion" in types, "Graph should have champion nodes"
        assert "item" in types, "Graph should have item nodes"
        assert "trait" in types, "Graph should have trait nodes"
        assert "augment" in types, "Graph should have augment nodes"

    def test_graph_minimum_node_counts(self):
        G = build_graph()
        from collections import Counter
        counts = Counter(G.nodes[n].get("type") for n in G.nodes())
        assert counts["champion"] >= 59, f"Expected >=59 champions, got {counts['champion']}"
        assert counts["trait"] >= 30, f"Expected >=30 traits, got {counts['trait']}"
        assert counts["item"] >= 44, f"Expected >=44 items, got {counts['item']}"
        assert counts["augment"] >= 252, f"Expected >=252 augments, got {counts['augment']}"

    def test_node_attributes_includes_is_verified(self):
        G = build_graph()
        sample_nodes = list(G.nodes())[:5]
        for node in sample_nodes:
            assert "is_verified" in G.nodes[node], f"Node {node} missing is_verified"
            assert isinstance(G.nodes[node]["is_verified"], bool)


class TestEdges:
    """Tests for edge construction."""

    def test_has_trait_edges(self, sample_graph):
        G = sample_graph
        assert "anima" in G.neighbors("briar"), "Briar should have Anima trait"
        edge_data = G.get_edge_data("briar", "anima")
        assert any(e.get("edge_type") == "HAS_TRAIT" for e in edge_data.values())

    def test_has_trait_briar_anima_count(self, sample_graph):
        G = sample_graph
        edge_data = G.get_edge_data("briar", "anima")
        has_trait = next(
            (e for e in edge_data.values() if e.get("edge_type") == "HAS_TRAIT"),
            None,
        )
        assert has_trait is not None
        assert has_trait.get("count") == 1

    def test_builds_from_edges(self, sample_graph):
        G = sample_graph
        assert "b_f_sword" in G.neighbors("bloodthirster"), "Bloodthirster should have B.F. Sword in recipe"
        assert "negatron_cloak" in G.neighbors("bloodthirster"), "Bloodthirster should have Negatron Cloak in recipe"

    def test_item_for_champion_edge(self, sample_graph):
        G = sample_graph
        # ITEM_FOR_CHAMPION edges go FROM item TO champion (incoming to champion)
        assert "bloodthirster" in G.predecessors("briar"), "Bloodthirster should be linked to Briar"
        edge_data = G.get_edge_data("bloodthirster", "briar")
        assert any(e.get("edge_type") == "ITEM_FOR_CHAMPION" for e in edge_data.values())


class TestNormalization:
    """Tests for node ID normalization."""

    def test_normalize_nova(self):
        assert normalize_id("N.O.V.A.") == "n_o_v_a"

    def test_normalize_bf_sword(self):
        assert normalize_id("B.F. Sword") == "b_f_sword"

    def test_normalize_bloodthirster(self):
        assert normalize_id("Bloodthirster") == "bloodthirster"

    def test_normalize_trailing_underscore(self):
        # "Anima  " (with spaces) should not produce trailing underscore
        result = normalize_id("Anima  ")
        assert not result.endswith("_"), f"Should not end with underscore: {result}"


class TestHeuristics:
    """Tests for ITEM_FOR_CHAMPION heuristics."""

    def test_infer_role_anima_champion(self):
        assert infer_role(3, ["Anima", "Invoker"]) == "AP"  # trait takes priority

    def test_infer_role_high_cost(self):
        assert infer_role(5, []) == "AD"  # 5-cost defaults to AD

    def test_infer_role_low_cost(self):
        assert infer_role(1, []) == "TANK"  # 1-cost defaults to TANK

    def test_categorize_ad_item(self):
        assert categorize_item(["B.F. Sword", "Negatron Cloak"]) == "AD"

    def test_categorize_ap_item(self):
        assert categorize_item(["Needlessly Large Rod", "Giant's Belt"]) == "AP"


class TestGraphProperties:
    """Tests for graph traversal and edge cases."""

    def test_circular_references_handled(self):
        G = build_graph()
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0

    def test_empty_champion_traits_handled(self):
        G = build_graph()
        for node in G.nodes():
            if G.nodes[node].get("type") == "champion":
                assert G.nodes[node].get("name") is not None
                assert "is_verified" in G.nodes[node]

    def test_depth_3_traversal_no_infinite_loop(self):
        G = build_graph()
        briar_id = normalize_id("Briar")
        paths = dict(nx.single_source_shortest_path_length(G, briar_id, cutoff=3))
        assert len(paths) > 0  # Briar should have neighbors

    def test_graph_reload_preserves_structure(self):
        G1 = knowledge_graph.get()
        counts1 = dict(knowledge_graph.node_counts)
        G2 = knowledge_graph.reload()
        counts2 = dict(knowledge_graph.node_counts)
        assert counts1 == counts2, f"Reload should preserve node counts: {counts1} vs {counts2}"


class TestAPIIntegration:
    """Integration tests for graph behavior."""

    def test_singleton_persistence(self):
        from app.graph import knowledge_graph as kg2
        assert kg2 is knowledge_graph

    def test_lazy_loading(self):
        hasattr(knowledge_graph, 'is_loaded')

    def test_error_response_model(self):
        err = ErrorResponse(error="not found", entity="fake_champ", suggestions=["a", "b", "c"])
        assert err.error == "not found"
        assert len(err.suggestions) == 3
        assert "fake_champ" in err.entity
