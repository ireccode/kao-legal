"""FastAPI application entry point."""

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from kao_legal.api.routes import credits, documents, meeting, webhooks
from kao_legal.config.settings import get_settings

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Kao Legal API",
        version="0.1.0",
        docs_url="/docs" if settings.environment == "development" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meeting.router)
    app.include_router(documents.router)
    app.include_router(credits.router)
    app.include_router(webhooks.router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "environment": settings.environment}

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()

# Lambda handler via Mangum
handler = Mangum(app, lifespan="off")
