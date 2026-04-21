"""Debug search endpoint for RAG retrieval quality inspection."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models import SearchRequest
from app.services.retrieval import retrieve_chunks

router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
async def search(request: SearchRequest) -> dict:
    """Search the knowledge base using hybrid retrieval.

    Returns top chunks with scores for debugging retrieval quality.
    """
    try:
        chunks = await retrieve_chunks(request.query, top_k=request.top_k)
        return {
            "query": request.query,
            "top_k": request.top_k,
            "chunks": [
                {
                    "id": c["id"],
                    "source": c["source"],
                    "heading": c.get("metadata", {}).get("heading_path", ""),
                    "text": c["content"],
                    "score": c["score"],
                }
                for c in chunks
            ],
            "count": len(chunks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
