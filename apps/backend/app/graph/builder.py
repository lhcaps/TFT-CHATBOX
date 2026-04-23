"""Knowledge graph construction from TFT JSON data sources."""
from __future__ import annotations

import re
from typing import Any
from pathlib import Path

import networkx as nx

from app.graph.loader import load_json


def normalize_id(name: str) -> str:
    """Normalize entity name to a safe graph node ID.
    
    Examples:
        "N.O.V.A."     → "n_o_v_a"
        "B.F. Sword"   → "b_f_sword"
        "Bloodthirster" → "bloodthirster"
        "anima  "       → "anima"
    """
    return re.sub(r'[^a-z0-9]+', '_', name.lower().strip()).strip('_')


def _safe_get(d: dict, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested dict keys."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
        if d is None:
            return default
    return d


def build_graph() -> nx.MultiDiGraph:
    """Build a MultiDiGraph from all TFT JSON data sources.
    
    Node types: champion, item, trait, augment, god, system
    Edge types: HAS_TRAIT, BUILDS_FROM, ITEM_FOR_CHAMPION, TRAIT_BREAKPOINT
    
    Sources (in load order):
      1. tft_set17_patch17_1_data_pack.json         — champions + trait list
      2. tft_set17_patch17_1_deep_pack_v4_user_verified.json — trait details + champions-per-trait
      3. items_formulas_full_set17.json             — items + recipes
      4. augments_full_user_verified.json           — augments
      5. traits_full_user_verified.json              — additional trait text
      6. tft_set17_patch17_1_enhanced_pack.json     — Space Gods (gods) + systems
      7. rolling_odds_user_verified.json            — rolling odds system
    """
    G = nx.MultiDiGraph()

    # ── 1. Data Pack: champions + origin/class trait list ──────────────────────
    try:
        data_pack = load_json("tft_set17_patch17_1_data_pack.json")
    except FileNotFoundError:
        data_pack = {}

    origins: list[dict] = _safe_get(data_pack, "origins", default=[])
    classes: list[dict] = _safe_get(data_pack, "classes", default=[])
    champions_raw: list[dict] = _safe_get(data_pack, "champions", default=[])

    # ── 2. Deep Pack v4: origins + classes detail + champions-per-trait ─────────
    try:
        deep_pack = load_json("tft_set17_patch17_1_deep_pack_v4_user_verified.json")
    except FileNotFoundError:
        deep_pack = {}

    deep_origins: dict = _safe_get(deep_pack, "traits_numeric", "origins", default={})
    deep_classes: dict = _safe_get(deep_pack, "traits_numeric", "classes", default={})
    user_verified: dict = _safe_get(deep_pack, "user_verified_tftactics_override", "traits_and_classes", default={})

    # Build complete trait detail map: prefer deep_pack, fallback to user_verified
    trait_detail: dict[str, dict] = {}
    for name, data in {**deep_origins, **deep_classes}.items():
        trait_detail[name] = data
    for name, data in user_verified.items():
        if name not in trait_detail:
            trait_detail[name] = data
        else:
            # Merge: keep breakpoints from deep_pack, champions from user_verified
            trait_detail[name].setdefault("breakpoints", data.get("breakpoints"))
            trait_detail[name].setdefault("effect", data.get("effect"))

    # Collect all known origin names
    origin_names: set[str] = set(deep_origins.keys())

    # ── 3. Add champion nodes ──────────────────────────────────────────────────
    for champ in champions_raw:
        name = champ.get("name", "")
        if not name:
            continue
        champ_id = normalize_id(name)
        traits_list = champ.get("traits", [])
        cost = champ.get("cost", 0)
        G.add_node(
            champ_id,
            type="champion",
            name=name,
            cost=cost,
            traits=traits_list,
            is_verified=True,
        )

    # ── 4. Add trait nodes ────────────────────────────────────────────────────
    for origin in origins:
        t_name = origin.get("name", "")
        if not t_name:
            continue
        tid = normalize_id(t_name)
        breakpoints = origin.get("breakpoints", [])
        # Determine trait_type
        trait_type = "origin" if t_name in origin_names else "class"
        G.add_node(
            tid,
            type="trait",
            name=t_name,
            trait_type=trait_type,
            breakpoints=breakpoints,
            is_verified=True,
        )

    for cls_item in classes:
        t_name = cls_item.get("name", "")
        if not t_name:
            continue
        tid = normalize_id(t_name)
        if G.has_node(tid):
            continue  # already added from origins
        G.add_node(
            tid,
            type="trait",
            name=t_name,
            trait_type="class",
            breakpoints=cls_item.get("breakpoints", []),
            is_verified=True,
        )

    # ── 5. Add SystemNode for realm_of_the_gods ───────────────────────────────
    try:
        enhanced = load_json("tft_set17_patch17_1_enhanced_pack.json")
        systems = _safe_get(enhanced, "systems", default={})
        if "realm_of_the_gods" in systems:
            G.add_node(
                "realm_of_the_gods",
                type="system",
                name="Realm of the Gods",
                description=systems["realm_of_the_gods"].get("summary", ""),
                is_verified=True,
            )
    except FileNotFoundError:
        pass

    # ── 6. Add GodNodes (Space Gods) ──────────────────────────────────────────
    try:
        if "space_gods" in systems:
            for god in systems["space_gods"]:
                god_name = god.get("name", "")
                if not god_name:
                    continue
                god_id = normalize_id(god_name) + "_god"
                G.add_node(
                    god_id,
                    type="god",
                    name=god_name,
                    focus=god.get("focus", ""),
                    is_verified=True,
                )
    except NameError:
        pass  # enhanced not loaded

    # ── 7. Add rolling odds as SystemNode ─────────────────────────────────────
    try:
        rolling = load_json("rolling_odds_user_verified.json")
        G.add_node(
            "rolling_odds",
            type="system",
            name="Rolling Odds",
            pool_sizes=_safe_get(rolling, "unit_pool_sizes", default={}),
            is_verified=True,
        )
    except FileNotFoundError:
        pass

    # ── 8. Load items ──────────────────────────────────────────────────────────
    items_raw: list[dict] = []
    try:
        items_formulas = load_json("items_formulas_full_set17.json")
        # Load ALL item categories
        item_keys = [
            "standard_combined_items",
            "combined_items",
            "combined",
            "radiant_items",
            "artifacts",
            "psionic_items",
            "anima_weapon_examples",
            "tactician_items",
            "emblems",
        ]
        for key in item_keys:
            items = _safe_get(items_formulas, key, default=[])
            for item in items:
                item["_source"] = key
                items_raw.append(item)
    except FileNotFoundError:
        pass

    # Deduplicate by name
    seen_items: dict[str, dict] = {}
    for item in items_raw:
        name = item.get("name", "")
        if name and name not in seen_items:
            seen_items[name] = item
    items_raw = list(seen_items.values())

    # ── 9. Add item nodes + BUILDS_FROM edges ─────────────────────────────────
    for item in items_raw:
        name = item.get("name", "")
        if not name:
            continue
        iid = normalize_id(name)
        recipe = item.get("recipe", [])
        completeness = item.get("completeness", "full")
        is_verified = completeness != "partial"

        G.add_node(
            iid,
            type="item",
            name=name,
            category=item.get("category", "standard"),
            recipe=recipe,
            completeness=completeness,
            is_verified=is_verified,
        )
        for comp in recipe:
            comp_id = normalize_id(comp)
            # Add component node if not exists
            if comp_id not in G:
                G.add_node(
                    comp_id,
                    type="item",
                    name=comp,
                    category="component",
                    recipe=[],
                    is_verified=True,
                )
            G.add_edge(
                iid, comp_id,
                edge_type="BUILDS_FROM",
                role="component",
            )

    # ── 10. Load augments ─────────────────────────────────────────────────────
    try:
        augments_data = load_json("augments_full_user_verified.json")
        augments_list = _safe_get(augments_data, "augments", default=[])
    except FileNotFoundError:
        augments_list = []

    seen_augment_ids: set[str] = set()
    for aug in augments_list:
        name = aug.get("name", "")
        if not name:
            continue
        aid = normalize_id(name)
        # Handle normalize_id collisions (e.g., "Advanced Loan" vs "Advanced Loan+")
        suffix = ""
        while aid + suffix in seen_augment_ids:
            suffix_count = int(suffix.lstrip("_") or 0) + 1
            suffix = f"_{suffix_count}"
        final_id = aid + suffix
        seen_augment_ids.add(final_id)
        G.add_node(
            final_id,
            type="augment",
            name=name,
            tier=aug.get("tier", "Silver"),
            description=aug.get("description", ""),
            is_verified=True,
        )

    # ── 11. HAS_TRAIT edges ────────────────────────────────────────────────────
    # Build reverse index: trait_name → [champion_names]
    trait_champions: dict[str, list[str]] = {}
    for champ in champions_raw:
        champ_name = champ.get("name", "")
        for trait_name in champ.get("traits", []):
            trait_champions.setdefault(trait_name, []).append(champ_name)

    for champ in champions_raw:
        champ_name = champ.get("name", "")
        champ_id = normalize_id(champ_name)
        if champ_id not in G:
            continue
        for trait_name in champ.get("traits", []):
            trait_id = normalize_id(trait_name)
            if trait_id in G:
                # Count how many champions have this trait (for breakpoint threshold)
                count = len(trait_champions.get(trait_name, []))
                G.add_edge(
                    champ_id, trait_id,
                    edge_type="HAS_TRAIT",
                    count=count,
                )

    # ── 12. TRAIT_BREAKPOINT edges ────────────────────────────────────────────
    for trait_name, tdata in trait_detail.items():
        tid = normalize_id(trait_name)
        if tid not in G:
            continue
        bps = tdata.get("breakpoints", [])
        if not isinstance(bps, list):
            continue
        tiers = tdata.get("tiers", {}) or tdata.get("tier_bonuses", {})
        for bp in bps:
            bonus = None
            if isinstance(tiers, dict) and str(bp) in tiers:
                bonus = tiers[str(bp)]
            G.add_edge(
                tid, tid,
                edge_type="TRAIT_BREAKPOINT",
                count=bp,
                bonus=bonus,
            )

    # ── 13. ITEM_FOR_CHAMPION edges (heuristic) ───────────────────────────────
    from app.graph.heuristics import assign_item_edges
    assign_item_edges(G, champions_raw, items_raw)

    return G
