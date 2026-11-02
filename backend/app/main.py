"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import cliq, proposals, projects, salesiq
from app.config import get_settings
from app.database.session import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("scopepilot")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ScopePilot AI starting (env=%s)", settings.app_env)
    # In production you would run Alembic migrations here or via entrypoint
    yield
    await engine.dispose()
    logger.info("ScopePilot AI shutdown")


app = FastAPI(
    title="ScopePilot AI",
    description="Intelligent project scoping and proposal automation platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# Mount routers
prefix = settings.api_prefix
app.include_router(projects.router, prefix=prefix)
app.include_router(proposals.router, prefix=prefix)
app.include_router(salesiq.router, prefix=prefix)
app.include_router(cliq.router, prefix=prefix)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "scopepilot-ai"}


@app.get("/")
async def root():
    return {
        "service": "ScopePilot AI",
        "version": "0.1.0",
        "docs": "/docs",
        "architecture": "2 LLM agents (Llama + Mistral via OpenRouter) + deterministic shell agents",
    }
