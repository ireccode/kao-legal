"""FastAPI application entry point."""

import json
import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from kao_legal.api.routes import credits, documents, meeting, webhooks, jobs
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
    app.include_router(jobs.router)

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
_mangum_handler = Mangum(app, lifespan="off")


# ---------------------------------------------------------------------------
# Smart Lambda handler: routes async job events OR normal HTTP events
# ---------------------------------------------------------------------------

_JOB_PROCESSORS = {
    "meeting_summary": "kao_legal.api.routes.meeting:process_meeting_summary_job",
}


def handler(event: dict, context) -> dict:
    """
    Lambda entry point.

    Handles two event shapes:
      1. { "_async_job": { "job_id": "...", "job_type": "..." } }
         -> runs the background job (invoked asynchronously by fire_async_lambda)
      2. API Gateway proxy event (normal HTTP request)
         -> handled by Mangum/FastAPI
    """
    async_job = event.get("_async_job")
    if async_job:
        job_id = async_job["job_id"]
        job_type = async_job["job_type"]
        logger.info("Processing async job", job_id=job_id, job_type=job_type)

        # Load job payload from DynamoDB
        from kao_legal.api.routes.jobs import get_job, update_job_status, JobStatus
        job = get_job(job_id)
        if not job:
            logger.error("Job not found", job_id=job_id)
            return {"statusCode": 404}

        payload = json.loads(job["payload"])

        # Dispatch to the right worker
        processor_ref = _JOB_PROCESSORS.get(job_type)
        if not processor_ref:
            update_job_status(job_id, JobStatus.FAILED, error=f"Unknown job type: {job_type}")
            return {"statusCode": 400}

        module_path, func_name = processor_ref.split(":")
        import importlib
        module = importlib.import_module(module_path)
        processor = getattr(module, func_name)
        processor(job_id, payload)
        return {"statusCode": 200}

    # Normal API Gateway HTTP event
    return _mangum_handler(event, context)

