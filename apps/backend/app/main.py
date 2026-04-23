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

from app.routes import health, sessions, chat, search, ingest, patch_state, gpu_status, graph, watch  # noqa: E402, F401

app.include_router(health.router, prefix="/api")
app.include_router(gpu_status.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(patch_state.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(watch.router, prefix="/api")

# Register graph reload → cache invalidation callback
from app.graph.events import on_graph_reload
from app.services.cache import embedding_cache
on_graph_reload(lambda: embedding_cache.clear())
