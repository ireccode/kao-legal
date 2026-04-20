"""Meeting summary API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from kao_legal.agents.legal_advisor_agent import create_legal_advisor_agent
from kao_legal.agents.meeting_summary_workflow import MeetingInput, run_meeting_summary
from kao_legal.api.middleware.auth import verify_cognito_token
from kao_legal.api.routes.credits import (
    CREDITS_PER_MEETING_SUMMARY,
    InsufficientCreditsError,
    deduct_credits,
)

router = APIRouter(prefix="/api/v1/meeting", tags=["meeting"])


class MeetingSummaryRequest(BaseModel):
    transcript_or_notes: str = Field(..., min_length=50)
    lawyer_name: str
    client_code: str
    client_name: str
    matter_id: str
    meeting_date: str
    jurisdiction: str = ""
    topic_tags: list[str] = []


class MeetingSummaryResponse(BaseModel):
    meeting_summary: str
    agreed_actions: list[str]
    deadlines: list[str]
    open_questions: list[str]
    email_subject: str
    email_body_text: str
    email_body_html: str
    s3_summary_key: str
    credits_consumed: int


@router.post("/summary", response_model=MeetingSummaryResponse)
async def create_meeting_summary(
    request: MeetingSummaryRequest,
    claims: dict = Depends(verify_cognito_token),
) -> MeetingSummaryResponse:
    """
    Generate a structured meeting summary and client email draft.

    Requires authentication and deducts credits from user account.
    """
    lawyer_id = claims["sub"]

    try:
        deduct_credits(lawyer_id, CREDITS_PER_MEETING_SUMMARY)
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Need {e.required} credits.",
        ) from e

    try:
        meeting_date = datetime.fromisoformat(request.meeting_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid meeting_date format: {request.meeting_date}",
        ) from e

    agent = create_legal_advisor_agent()
    meeting_input = MeetingInput(
        transcript_or_notes=request.transcript_or_notes,
        lawyer_id=lawyer_id,
        lawyer_name=request.lawyer_name,
        client_code=request.client_code,
        client_name=request.client_name,
        matter_id=request.matter_id,
        meeting_date=meeting_date,
        jurisdiction=request.jurisdiction,
        topic_tags=request.topic_tags,
    )

    output = run_meeting_summary(meeting_input, agent=agent)

    return MeetingSummaryResponse(
        meeting_summary=output.meeting_summary,
        agreed_actions=output.agreed_actions,
        deadlines=output.deadlines,
        open_questions=output.open_questions,
        email_subject=output.email_subject,
        email_body_text=output.email_body_text,
        email_body_html=output.email_body_html,
        s3_summary_key=output.s3_summary_key,
        credits_consumed=CREDITS_PER_MEETING_SUMMARY,
    )
