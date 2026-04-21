"""Chat endpoints with streaming support and conversation history."""
from __future__ import annotations

import json
from collections.abc import AsyncIterable

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.sse import ServerSentEvent

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
) -> list[dict]:
    """Build the messages array for Ollama: system + recent history + user."""
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

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages


async def stream_ollama_tokens(
    messages: list[dict],
    session_id: str,
) -> AsyncIterable[str]:
    """Stream tokens from Ollama as structured SSE events."""
    full_text = ""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

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

    - stream=true: SSE with token/done/usage events
    - stream=false: JSON with text/usage/done_reason/citations

    Per D-09: Single endpoint with stream parameter (default True).
    """
    if request.session_id is None:
        raise HTTPException(status_code=400, detail="session_id is required")

    # Build messages array with system prompt + history
    messages = await build_messages(
        session_id=request.session_id,
        user_message=request.message,
        mode=request.mode,
    )

    # Persist the user message BEFORE streaming (so it appears in history)
    pool = await get_pool()
    msg_repo = MessageRepository(pool)
    await msg_repo.create(
        session_id=request.session_id,
        role="user",
        content=request.message,
        metadata={},
    )

    if request.stream:
        # Streaming mode: SSE with structured events
        return StreamingResponse(
            stream_ollama_tokens(messages, request.session_id),
            media_type="text/event-stream"
        )
    else:
        # Non-streaming mode: return complete JSON
        result = await chat_non_streaming(messages, request.session_id)
        return JSONResponse(content=result)
