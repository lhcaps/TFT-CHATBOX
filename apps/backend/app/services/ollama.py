"""Ollama service for LLM and embedding calls."""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class OllamaService:
    """Client for Ollama API."""

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.chat_model = settings.ollama_chat_model
        self.embedding_model = settings.ollama_embedding_model

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for the given text."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": self.embedding_model,
                "input": text,
            }
            response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])

    async def chat(self, messages: list[dict[str, Any]], stream: bool = True) -> httpx.Response:
        """Send a chat request to Ollama."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": self.chat_model,
                "messages": messages,
                "stream": stream,
            }
            return await client.post(f"{self.base_url}/api/chat", json=payload)


ollama = OllamaService()
