"""Application configuration from environment variables."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:54322/postgres"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embedding_model: str = "qwen3-embedding:4b"
    ollama_embedding_dims: int = 1024

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # RAG
    rag_top_k: int = 15
    rag_chunk_size: int = 2000
    rag_chunk_overlap: int = 500

    # Obsidian
    obsidian_vault_path: str = ""

    # Ollama keep_alive
    ollama_keep_alive: str = "15m"

    # Chat
    chat_history_window: int = 10

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3001"]

    # n8n
    webhook_url: str = "http://localhost:5678/"
    n8n_proxy_hops: int = 1
    generic_timezone: str = "Asia/Ho_Chi_Minh"
    tz: str = "Asia/Ho_Chi_Minh"

    # TFT Cache
    tft_cache_dir: str = str(Path.home() / ".tft-copilot" / "cache")

    # Embedding cache (POLY-01)
    embedding_cache_max_size: int = 500
    embedding_cache_ttl_seconds: int = 1800  # 30 minutes

    # API Auth
    api_secret_key: str = ""


settings = Settings()
