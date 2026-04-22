"""
Async job management: submit/poll pattern for long-running agent tasks.

Why this exists:
    API Gateway REST API has a hard 29-second timeout that cannot be changed.
    The Bedrock agent workflow takes 60-180 seconds. Rather than returning a
    timeout error, we:
      1. POST -> accepts job, deducts credits, fires async Lambda, returns job_id
      2. GET  -> client polls /jobs/{job_id} until status == "completed" | "failed"
      3. On failure the worker Lambda refunds credits via the jobs table marker.
"""

import json
import time
import uuid
from enum import Enum
from typing import Any

import boto3
import structlog
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status

from kao_legal.api.middleware.auth import verify_cognito_token
from kao_legal.config.settings import get_settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

JOB_TTL_SECONDS = 86_400  # 24 hours


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# DynamoDB helpers
# ---------------------------------------------------------------------------


def _jobs_table():
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(settings.dynamodb_jobs_table)


def create_job(job_type: str, payload: dict, user_id: str) -> str:
    """Create a new job record and return the job_id."""
    job_id = str(uuid.uuid4())
    now = int(time.time())
    _jobs_table().put_item(
        Item={
            "job_id": job_id,
            "job_type": job_type,
            "status": JobStatus.PENDING,
            "user_id": user_id,
            "payload": json.dumps(payload),
            "created_at": now,
            "ttl": now + JOB_TTL_SECONDS,
        }
    )
    return job_id


def get_job(job_id: str) -> dict | None:
    """Fetch a job record by ID."""
    response = _jobs_table().get_item(Key={"job_id": job_id})
    return response.get("Item")


def update_job_status(
    job_id: str,
    new_status: JobStatus,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    """Update a job's status (and optionally store result/error)."""
    update_expr = "SET #s = :s, updated_at = :ts"
    names = {"#s": "status"}
    values: dict[str, Any] = {":s": new_status.value, ":ts": int(time.time())}

    if result is not None:
        update_expr += ", result = :r"
        values[":r"] = json.dumps(result)
    if error is not None:
        update_expr += ", #e = :e"
        names["#e"] = "error"
        values[":e"] = error

    _jobs_table().update_item(
        Key={"job_id": job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def fire_async_lambda(job_id: str, job_type: str) -> None:
    """
    Invoke THIS Lambda asynchronously with a special event so it runs
    the job in the background without blocking the HTTP response.
    """
    settings = get_settings()
    if not settings.lambda_function_name:
        # Local dev fallback — run synchronously (will be slow but won't hang)
        logger.warning("LAMBDA_FUNCTION_NAME not set; cannot fire async job")
        return

    lambda_client = boto3.client("lambda", region_name=settings.aws_region)
    lambda_client.invoke(
        FunctionName=settings.lambda_function_name,
        InvocationType="Event",  # async — fire and forget
        Payload=json.dumps({"_async_job": {"job_id": job_id, "job_type": job_type}}),
    )
    logger.info("Async job fired", job_id=job_id, job_type=job_type)


# ---------------------------------------------------------------------------
# GET /api/v1/jobs/{job_id}  — poll for result
# ---------------------------------------------------------------------------


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    claims: dict = Depends(verify_cognito_token),
) -> dict:
    """Poll a background job for its current status and result."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Security: only the owning user can read the job
    if job.get("user_id") != claims["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    response: dict[str, Any] = {
        "job_id": job_id,
        "status": job["status"],
        "job_type": job.get("job_type"),
        "created_at": job.get("created_at"),
    }

    # Edge case: Lambda was killed mid-flight (timeout) after writing error but
    # before updating status to "failed". Treat these as failed for the client.
    if job["status"] == JobStatus.RUNNING and job.get("error"):
        response["status"] = JobStatus.FAILED
        response["error"] = job["error"]
        # Best-effort heal the DynamoDB record
        try:
            update_job_status(job_id, JobStatus.FAILED, error=job["error"])
        except Exception:
            pass
        return response

    if job["status"] == JobStatus.COMPLETED and job.get("result"):
        response["result"] = json.loads(job["result"])

    if job["status"] == JobStatus.FAILED:
        response["error"] = job.get("error", "Unknown error")

    return response
