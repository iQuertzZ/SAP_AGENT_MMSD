"""
SAP MM/SD AI Copilot — FastAPI application entry point.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import analyze, approval, execution, health, simulate
from backend.app.core.config import settings
from backend.app.core.exceptions import CopilotBaseError
from backend.app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    configure_logging()
    logger.info(
        "SAP MM/SD Copilot starting",
        env=settings.app_env,
        connector=settings.sap_connector,
        ai_enabled=settings.ai_enabled,
        execution_enabled=settings.execution_enabled,
    )
    yield
    logger.info("SAP MM/SD Copilot shutting down")


app = FastAPI(
    title="SAP MM/SD AI Copilot",
    description=(
        "Enterprise-grade AI Copilot for SAP Materials Management and Sales & Distribution. "
        "Diagnoses issues, recommends actions, simulates impact, and executes safely."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CopilotBaseError)
async def copilot_error_handler(request: Request, exc: CopilotBaseError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )


# ── API routes ───────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(health.router, prefix=PREFIX, tags=["Health"])
app.include_router(analyze.router, prefix=PREFIX, tags=["Analysis"])
app.include_router(simulate.router, prefix=PREFIX, tags=["Simulation"])
app.include_router(approval.router, prefix=PREFIX, tags=["Approval"])
app.include_router(execution.router, prefix=PREFIX, tags=["Execution"])

# ── Static frontend ──────────────────────────────────────────────────────────
import os

_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_FRONTEND):
    app.mount("/static", StaticFiles(directory=_FRONTEND), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_ui() -> FileResponse:
        return FileResponse(os.path.join(_FRONTEND, "index.html"))
