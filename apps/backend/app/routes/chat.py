"""Chat endpoints with streaming support."""
from __future__ import annotations

from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


async def stream_ollama_response(messages: list[dict], session_id: str) -> AsyncGenerator[str, None]:
    """Stream responses from Ollama."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "model": settings.ollama_chat_model,
            "messages": messages,
            "stream": True,
        }
        async with client.stream("POST", f"{settings.ollama_base_url}/api/chat", json=payload) as response:
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Ollama unavailable")
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield f"data: {content}\n\n"
                    except json.JSONDecodeError:
                        continue


@router.post("")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream a chat response from Ollama."""
    messages = [{"role": "user", "content": request.message}]
    return StreamingResponse(
        stream_ollama_response(messages, request.session_id or ""),
        media_type="text/event-stream",
    )
