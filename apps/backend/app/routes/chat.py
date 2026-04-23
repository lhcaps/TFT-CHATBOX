"""Chat endpoints with streaming support and conversation history."""
from __future__ import annotations

import json
from collections.abc import AsyncIterable

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import settings
from app.db import get_pool
from app.models import ChatRequest
from app.prompts import get_system_prompt
from app.repositories.message import MessageRepository


router = APIRouter(prefix="/chat", tags=["chat"])


async def build_messages(
    session_id: str,
    user_message: str,
    mode: str,
    patch: str | None = None,
    top_k: int | None = None,
    router_result: dict | None = None,  # NEW: from QueryRouter
) -> list[dict]:
    """Build the messages array for Ollama: system + recent history + optional RAG context."""
    pool = await get_pool()
    repo = MessageRepository(pool)

    # Get recent non-system messages (per D-01 to D-03)
    recent = await repo.get_recent(session_id, settings.chat_history_window)

    messages: list[dict] = []

    # Add system prompt (not counted in window — per D-02)
    system_prompt = get_system_prompt(mode)
    messages.append({"role": "system", "content": system_prompt})

    # Add conversation history (oldest first)
    for msg in recent:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Inject RAG context for rag/coach modes
    effective_top_k = top_k if top_k is not None else settings.rag_top_k
    if mode in ("rag", "coach"):
        from app.services.retrieval import retrieve_chunks
        chunks = await retrieve_chunks(user_message, top_k=effective_top_k, patch=patch)
        if chunks:
            context_lines = ["---CONTEXT---"]
            for i, chunk in enumerate(chunks, 1):
                heading = chunk.get("metadata", {}).get("heading_path", "")
                source = chunk.get("source", "unknown")
                heading_str = f" > {heading}" if heading else ""
                context_lines.append(f"[{i}] From: {source}{heading_str}")
                context_lines.append(chunk["content"][:500])  # truncate for prompt safety
                context_lines.append("")
            context_lines.append("---CONTEXT---")
            context_block = "\n".join(context_lines)
            messages.append({"role": "user", "content": context_block})

    # Inject graph context if available (from QueryRouter)
    if router_result and router_result.get("graph_data"):
        graph_data = router_result["graph_data"]
        if graph_data.get("neighbors"):
            graph_lines = ["---KNOWLEDGE GRAPH---"]
            entity = graph_data.get("entity", "Entity")
            graph_lines.append(f"Related data for: {entity}")
            for neighbor in graph_data["neighbors"][:5]:
                edge = neighbor.get("edge", "")
                node = neighbor.get("node", "")
                count = neighbor.get("count")
                count_str = f" ({count})" if count else ""
                graph_lines.append(f"  - {node}{count_str} [{edge}]")
            graph_lines.append("---END GRAPH---")
            graph_block = "\n".join(graph_lines)
            # Insert before user message (last message in list)
            messages.insert(len(messages) - 1, {"role": "system", "content": graph_block})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages


async def stream_ollama_tokens(
    messages: list[dict],
    session_id: str,
    mode: str = "normal",
    user_message: str = "",
    patch: str | None = None,
    top_k: int | None = None,
) -> AsyncIterable[str]:
    """Stream tokens from Ollama as structured SSE events.

    Emits citation events for rag/coach modes before the first token.
    """
    full_text = ""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    effective_top_k = top_k if top_k is not None else settings.rag_top_k

    # Emit citation events BEFORE streaming begins (rag/coach modes only)
    if mode in ("rag", "coach") and user_message:
        from app.services.retrieval import retrieve_chunks
        chunks = await retrieve_chunks(user_message, top_k=effective_top_k, patch=patch)
        for chunk in chunks:
            citation_data = {
                "id": chunk["id"],
                "source": chunk["source"],
                "heading": chunk.get("metadata", {}).get("heading_path", ""),
                "text": chunk["content"],
                "score": chunk["score"],
            }
            yield f"event: citation\ndata: {json.dumps({'citation': citation_data})}\n\n"

    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "model": settings.ollama_chat_model,
            "messages": messages,
            "stream": True,
            "keep_alive": settings.ollama_keep_alive,
            "options": {"num_ctx": 8192},
        }
        async with client.stream(
            "POST",
            f"{settings.ollama_base_url}/api/chat",
            json=payload,
        ) as response:
            if response.status_code != 200:
                yield f"event: error\ndata: {json.dumps({'error': 'Ollama unavailable'})}\n\n"
                return

            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_text += content
                        # Per D-04: token event format
                        yield f"event: token\ndata: {json.dumps({'token': content})}\n\n"

                    # Capture usage stats from done chunk (per D-06, D-07)
                    if chunk.get("done"):
                        usage["completion_tokens"] = chunk.get("eval_count", 0)
                        usage["prompt_tokens"] = chunk.get("prompt_eval_count", 0)
                        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
                        done_reason = chunk.get("done_reason", "stop")
                        # Per D-05: done event format
                        yield f"event: done\ndata: {json.dumps({'done': True, 'done_reason': done_reason, 'usage': usage})}\n\n"
                except json.JSONDecodeError:
                    continue

    # Persist the assistant message (after stream completes)
    try:
        pool = await get_pool()
        repo = MessageRepository(pool)
        await repo.create(
            session_id=session_id,
            role="assistant",
            content=full_text,
            metadata={"usage": usage},
        )
    except Exception:
        pass  # Don't fail the stream if DB write fails


async def chat_non_streaming(
    messages: list[dict],
    session_id: str,
) -> dict:
    """Get complete response from Ollama (non-streaming mode)."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "model": settings.ollama_chat_model,
            "messages": messages,
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {"num_ctx": 8192},
        }
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json=payload,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Ollama unavailable")

        data = response.json()
        full_text = data.get("message", {}).get("content", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        }

        # Persist assistant message
        pool = await get_pool()
        repo = MessageRepository(pool)
        await repo.create(
            session_id=session_id,
            role="assistant",
            content=full_text,
            metadata={"usage": usage},
        )

        # Per D-10: non-streaming response format
        return {
            "text": full_text,
            "usage": usage,
            "done_reason": data.get("done_reason", "stop"),
            "citations": [],
        }


@router.post("", response_model=None)
async def chat(request: ChatRequest) -> StreamingResponse | JSONResponse:
    """
    Chat endpoint with streaming and non-streaming modes.

    - stream=true: SSE with token/done/usage events (citation events for rag/coach)
    - stream=false: JSON with text/usage/done_reason/citations

    Per D-09: Single endpoint with stream parameter (default True).
    """
    import logging
    logger = logging.getLogger(__name__)

    if request.session_id is None:
        raise HTTPException(status_code=400, detail="session_id is required")

    router_result = None
    if request.mode in ("rag", "coach") and request.message:
        try:
            from app.services.router import QueryRouter
            router = QueryRouter()
            router_result = await router.route(request.message, top_k=request.top_k)
        except Exception as e:
            logger.warning(f"QueryRouter failed: {e}")
            router_result = None

    try:
        # Build messages array with system prompt + history + optional RAG context + graph context
        messages = await build_messages(
            session_id=request.session_id,
            user_message=request.message,
            mode=request.mode,
            patch=request.patch,
            top_k=request.top_k,
            router_result=router_result,
        )
    except Exception as e:
        logger.exception("build_messages failed")
        raise HTTPException(status_code=500, detail=f"build_messages error: {e}") from e

    # Persist the user message BEFORE streaming (so it appears in history)
    pool = await get_pool()
    msg_repo = MessageRepository(pool)
    # Auto-create session if it doesn't exist (for smoke tests and external callers)
    from app.repositories.session import SessionRepository
    sess_repo = SessionRepository(pool)
    existing = await sess_repo.get(request.session_id)
    if existing is None:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO sessions (id, title, mode) VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING",
                request.session_id,
                None,
                request.mode,
            )
    await msg_repo.create(
        session_id=request.session_id,
        role="user",
        content=request.message,
        metadata={},
    )

    if request.stream:
        # Streaming mode: SSE with structured events
        return StreamingResponse(
            stream_ollama_tokens(messages, request.session_id, request.mode, request.message, request.patch, request.top_k),
            media_type="text/event-stream",
        )
    else:
        # Non-streaming mode: return complete JSON
        try:
            result = await chat_non_streaming(messages, request.session_id)
            return JSONResponse(content=result)
        except Exception as e:
            logger.exception("chat_non_streaming failed")
            raise HTTPException(status_code=500, detail=f"chat_non_streaming error: {e}") from e
