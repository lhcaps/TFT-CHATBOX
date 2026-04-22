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
                "prompt": text,
            }
            response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding", [])
            if not isinstance(embedding, list):
                raise ValueError(f"Expected embedding list, got {type(embedding)}: {embedding}")
            return embedding

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in one batch request."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": self.embedding_model,
                "input": texts,
                "truncate": True,
            }
            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            if not isinstance(embeddings, list):
                raise ValueError(f"Expected embeddings list, got {type(embeddings)}")
            return embeddings

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
