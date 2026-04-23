"""Knowledge Graph module — NetworkX MultiDiGraph for TFT entities."""
from functools import lru_cache
from networkx import MultiDiGraph
import logging

logger = logging.getLogger(__name__)


class LazyGraphLoader:
    """Thread-safe lazy-loading wrapper around nx.MultiDiGraph.
    
    Defers graph construction until first access.
    Call reload() to rebuild from JSON files.
    """
    _instance: "LazyGraphLoader | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._graph: MultiDiGraph | None = None
            cls._instance._loaded = False
        return cls._instance

    def get(self) -> MultiDiGraph:
        if self._graph is None:
            from app.graph.builder import build_graph
            self._graph = build_graph()
            self._loaded = True
            logger.info(f"Knowledge graph loaded: {self._graph.number_of_nodes()} nodes, "
                       f"{self._graph.number_of_edges()} edges")
        return self._graph

    def reload(self) -> MultiDiGraph:
        """Clear and rebuild the graph from JSON sources."""
        logger.info("Reloading knowledge graph...")
        self._graph = None
        self._loaded = False
        return self.get()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def node_counts(self) -> dict[str, int]:
        """Return node counts by type."""
        from collections import Counter
        G = self.get()
        return dict(Counter(
            G.nodes[n].get("type", "unknown") for n in G.nodes()
        ))


# Singleton instance — import this instead of LazyGraphLoader()
knowledge_graph = LazyGraphLoader()
