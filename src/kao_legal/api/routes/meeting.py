"""Meeting summary API routes — async job pattern."""

import json
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from kao_legal.api.middleware.auth import verify_cognito_token
from kao_legal.api.routes.credits import (
    CREDITS_PER_MEETING_SUMMARY,
    InsufficientCreditsError,
    deduct_credits,
    refund_credits,
)
from kao_legal.api.routes.jobs import (
    JobStatus,
    create_job,
    fire_async_lambda,
    update_job_status,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/meeting", tags=["meeting"])

JOB_TYPE_MEETING = "meeting_summary"


class MeetingSummaryRequest(BaseModel):
    transcript_or_notes: str = Field(..., min_length=50)
    lawyer_name: str
    client_code: str
    client_name: str
    matter_id: str
    meeting_date: str
    jurisdiction: str = ""
    topic_tags: list[str] = []


# ---------------------------------------------------------------------------
# POST /api/v1/meeting/summary  — submit job (returns immediately)
# ---------------------------------------------------------------------------


@router.post("/summary", status_code=status.HTTP_202_ACCEPTED)
async def submit_meeting_summary(
    request: MeetingSummaryRequest,
    claims: dict = Depends(verify_cognito_token),
) -> dict:
    """
    Submit a meeting summary job. Returns a job_id immediately.

    The actual agent work runs asynchronously. Poll GET /api/v1/jobs/{job_id}
    for the result.

    Credits are deducted on submission and refunded if the job fails.
    """
    lawyer_id = claims["sub"]

    # Validate meeting_date before charging credits
    try:
        datetime.fromisoformat(request.meeting_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid meeting_date format: {request.meeting_date}",
        ) from e

    # Deduct credits upfront (refunded by worker on failure)
    try:
        deduct_credits(lawyer_id, CREDITS_PER_MEETING_SUMMARY)
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Need {e.required} credits.",
        ) from e

    # Persist job + fire async Lambda
    payload = {
        "lawyer_id": lawyer_id,
        "lawyer_name": request.lawyer_name,
        "client_code": request.client_code,
        "client_name": request.client_name,
        "matter_id": request.matter_id,
        "meeting_date": request.meeting_date,
        "jurisdiction": request.jurisdiction,
        "topic_tags": request.topic_tags,
        "transcript_or_notes": request.transcript_or_notes,
        "credits_deducted": CREDITS_PER_MEETING_SUMMARY,
    }
    job_id = create_job(JOB_TYPE_MEETING, payload, lawyer_id)
    fire_async_lambda(job_id, JOB_TYPE_MEETING)

    logger.info("Meeting summary job submitted", job_id=job_id, lawyer_id=lawyer_id)

    return {
        "job_id": job_id,
        "status": "pending",
        "poll_url": f"/api/v1/jobs/{job_id}",
        "message": "Job accepted. Poll poll_url for result (typically 30-120 seconds).",
    }


# ---------------------------------------------------------------------------
# Async worker entry point — called by fire_async_lambda
# ---------------------------------------------------------------------------


def process_meeting_summary_job(job_id: str, payload: dict) -> None:
    """
    Run the heavy Bedrock agent work. Called from the async Lambda handler.
    On success: writes result to jobs table.
    On failure: refunds credits and marks job as failed.
    """
    from kao_legal.agents.legal_advisor_agent import create_legal_advisor_agent
    from kao_legal.agents.meeting_summary_workflow import MeetingInput, run_meeting_summary

    lawyer_id = payload["lawyer_id"]
    credits_deducted = payload.get("credits_deducted", CREDITS_PER_MEETING_SUMMARY)

    update_job_status(job_id, JobStatus.RUNNING)

    try:
        meeting_date = datetime.fromisoformat(payload["meeting_date"])
        agent = create_legal_advisor_agent()
        meeting_input = MeetingInput(
            transcript_or_notes=payload["transcript_or_notes"],
            lawyer_id=lawyer_id,
            lawyer_name=payload["lawyer_name"],
            client_code=payload["client_code"],
            client_name=payload["client_name"],
            matter_id=payload["matter_id"],
            meeting_date=meeting_date,
            jurisdiction=payload.get("jurisdiction", ""),
            topic_tags=payload.get("topic_tags", []),
        )
        output = run_meeting_summary(meeting_input, agent=agent)

        result = {
            "meeting_summary": output.meeting_summary,
            "agreed_actions": output.agreed_actions,
            "deadlines": output.deadlines,
            "open_questions": output.open_questions,
            "email_subject": output.email_subject,
            "email_body_text": output.email_body_text,
            "email_body_html": output.email_body_html,
            "s3_summary_key": output.s3_summary_key,
            "credits_consumed": credits_deducted,
        }
        update_job_status(job_id, JobStatus.COMPLETED, result=result)
        logger.info("Meeting summary job completed", job_id=job_id)

    except Exception as exc:
        error_msg = str(exc)
        logger.error("Meeting summary job failed", job_id=job_id, error=error_msg)

        # Classify the error for the user
        err_lower = error_msg.lower()
        is_daily_limit = "too many tokens per day" in err_lower or "tokens per day" in err_lower
        is_throttle = "throttl" in err_lower or "too many requests" in err_lower

        if is_daily_limit:
            user_error = (
                "Bedrock daily token quota exceeded. "
                "Please try again tomorrow or contact support to increase your quota."
            )
        elif is_throttle:
            user_error = "Bedrock is temporarily throttled. Please retry in 60 seconds."
        else:
            user_error = f"Processing failed: {error_msg}"

        # Refund credits — always attempt this before marking failed
        try:
            refund_credits(lawyer_id, credits_deducted)
            logger.info(
                "Credits refunded after job failure",
                job_id=job_id,
                refunded=credits_deducted,
            )
        except Exception as refund_exc:
            logger.error("Failed to refund credits", job_id=job_id, error=str(refund_exc))

        # Write FAILED status — do NOT raise after this so the write always completes.
        # (The background Lambda has no caller awaiting a return value; the error is
        # already captured in CloudWatch logs via logger.error above.)
        update_job_status(job_id, JobStatus.FAILED, error=user_error)
