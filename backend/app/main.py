"""
SAP MM/SD AI Copilot — FastAPI application entry point.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import analyze, approval, execution, health, simulate
from backend.app.api.routes import auth as auth_router
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

    # ── DB health check + expired approval cleanup ──────────────────────────
    if settings.database_url:
        from backend.app.db.engine import AsyncSessionLocal
        from backend.app.db.repositories.approval_repository import ApprovalRepository

        try:
            if AsyncSessionLocal is not None:
                async with AsyncSessionLocal() as session:
                    repo = ApprovalRepository(session)
                    deleted = await repo.delete_expired()
                    await session.commit()
                logger.info("DB ready; expired approvals purged", count=deleted)
        except Exception as exc:
            logger.warning("DB health check failed", error=str(exc))

    # ── Seed first admin user ──────────────────────────────────────────────
    await _seed_admin()

    yield
    logger.info("SAP MM/SD Copilot shutting down")


async def _seed_admin() -> None:
    """Create the initial admin user if none exists (DB or in-memory)."""
    from backend.app.db.engine import AsyncSessionLocal
    from backend.app.db.repositories.user_repository import UserRepository
    from backend.app.models.auth import SAPRole
    from backend.app.services.auth_service import hash_password

    if AsyncSessionLocal is not None:
        async with AsyncSessionLocal() as session:
            repo = UserRepository(session)
            existing = await repo.get_by_email(settings.first_admin_email)
            if existing is None:
                await repo.create(
                    email=settings.first_admin_email,
                    hashed_password=hash_password(settings.first_admin_password),
                    role=SAPRole.ADMIN.value,
                    full_name="System Admin",
                )
                await session.commit()
                logger.info("First admin user created", email=settings.first_admin_email)
            else:
                logger.info("Admin user already exists", email=settings.first_admin_email)
    else:
        repo = UserRepository(None)  # in-memory fallback (no DB configured)
        existing = await repo.get_by_email(settings.first_admin_email)
        if existing is None:
            await repo.create(
                email=settings.first_admin_email,
                hashed_password=hash_password(settings.first_admin_password),
                role=SAPRole.ADMIN.value,
                full_name="System Admin",
            )
            logger.info("First admin user created", email=settings.first_admin_email)
        else:
            logger.info("Admin user already exists", email=settings.first_admin_email)


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


# ── API routes ────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(health.router, prefix=PREFIX, tags=["Health"])
app.include_router(auth_router.router, prefix=PREFIX)
app.include_router(analyze.router, prefix=PREFIX, tags=["Analysis"])
app.include_router(simulate.router, prefix=PREFIX, tags=["Simulation"])
app.include_router(approval.router, prefix=PREFIX, tags=["Approval"])
app.include_router(execution.router, prefix=PREFIX, tags=["Execution"])

# ── Static frontend ───────────────────────────────────────────────────────────
_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_FRONTEND):
    app.mount("/static", StaticFiles(directory=_FRONTEND), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_ui() -> FileResponse:
        return FileResponse(os.path.join(_FRONTEND, "index.html"))
