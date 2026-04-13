"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config.settings import get_settings
from stockpredict.db.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup / shutdown."""
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="StockPredict",
        description="Multi-horizon US equity analysis platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS for frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    from stockpredict.api.routes import analyze, auth, detail, history, status, watchlist
    app.include_router(auth.router, prefix="/api")
    app.include_router(analyze.router, prefix="/api")
    app.include_router(history.router, prefix="/api")
    app.include_router(detail.router, prefix="/api")
    app.include_router(status.router, prefix="/api")
    app.include_router(watchlist.router, prefix="/api")

    # Serve frontend static files in production
    frontend_dist = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app


app = create_app()
