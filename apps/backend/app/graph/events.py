"""Event system for knowledge graph reload signals."""
from __future__ import annotations

from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Module-level callback list
_reload_callbacks: list[Callable[[], None]] = []


def on_graph_reload(callback: Callable[[], None]) -> None:
    """Register a callback to be called when the graph reloads.
    
    Usage:
        from app.graph.events import on_graph_reload
        from app.services.cache import embedding_cache
        
        def clear_cache():
            embedding_cache.clear()
        
        on_graph_reload(clear_cache)
    """
    _reload_callbacks.append(callback)


def trigger_reload() -> None:
    """Trigger graph reload and call all registered callbacks.
    
    Called by:
    - POST /api/graph/reload (manual hot-reload)
    - ingest pipeline after successful ingest
    """
    from app.graph import knowledge_graph
    
    knowledge_graph.reload()
    logger.info(f"Graph reloaded, callbacks: {len(_reload_callbacks)}")
    
    for i, cb in enumerate(_reload_callbacks):
        try:
            cb()
            logger.info(f"Reload callback {i} succeeded")
        except Exception as e:
            logger.error(f"Reload callback {i} failed: {e}")
