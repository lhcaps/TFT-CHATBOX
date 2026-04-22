"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import close_pool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — startup and shutdown."""
    logger.info("Starting TFT Local Copilot API")
    logger.info(f"Ollama: {settings.ollama_base_url}")
    logger.info(f"Database: {settings.database_url}")
    yield
    logger.info("Shutting down TFT Local Copilot API")
    await close_pool()


app = FastAPI(
    title="TFT Local Copilot API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes import health, sessions, chat, search, ingest  # noqa: E402, F401

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(ingest.router)
