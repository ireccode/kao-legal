"""Meeting summary workflow orchestration."""

import json
from dataclasses import dataclass, field
from datetime import datetime

from strands import Agent

from kao_legal.agents.legal_advisor_agent import create_legal_advisor_agent


@dataclass
class MeetingInput:
    """Input for the meeting summary workflow."""

    transcript_or_notes: str
    lawyer_id: str
    lawyer_name: str
    client_code: str
    client_name: str
    matter_id: str
    meeting_date: datetime
    jurisdiction: str = ""
    topic_tags: list[str] = field(default_factory=list)


@dataclass
class MeetingOutput:
    """Output from the meeting summary workflow."""

    meeting_summary: str
    agreed_actions: list[str]
    deadlines: list[str]
    open_questions: list[str]
    email_subject: str
    email_body_text: str
    email_body_html: str
    s3_summary_key: str


_MEETING_PROMPT_TEMPLATE = (
    "Process the following meeting transcript/notes and produce a structured summary.\n\n"
    "MATTER DETAILS:\n"
    "- Matter ID: {matter_id}\n"
    "- Client: {client_code}\n"
    "- Lawyer: {lawyer_name}\n"
    "- Date: {meeting_date}\n"
    "- Jurisdiction: {jurisdiction}\n"
    "- Topics: {topic_tags}\n\n"
    "TRANSCRIPT/NOTES:\n"
    "{transcript_or_notes}\n\n"
    "REQUIRED STEPS:\n"
    "1. Extract a brief meeting_summary (2-4 sentences).\n"
    "2. List all agreed_actions as explicit instructions.\n"
    "3. List all deadlines and key dates mentioned.\n"
    "4. List open_questions requiring client confirmation.\n"
    '5. Call format_email_draft with lawyer_name="{lawyer_name}", '
    'client_name="{client_name}", matter_id="{matter_id}", '
    'jurisdiction="{jurisdiction}".\n'
    '6. Call export_summary with lawyer_id="{lawyer_id}", '
    'client_code="{client_code}", matter_id="{matter_id}", '
    'workflow_type="meeting_summary".\n'
    "7. Return the final structured JSON.\n\n"
    "Return ONLY valid JSON with keys: meeting_summary, agreed_actions, deadlines, "
    "open_questions, email_subject, email_body_text, email_body_html, s3_summary_key."
)


def run_meeting_summary(
    meeting_input: MeetingInput,
    agent: Agent | None = None,
) -> MeetingOutput:
    """
    Execute the post-meeting summary workflow.

    Args:
        meeting_input: Structured meeting data.
        agent: Optional pre-created agent (creates new one if not provided).

    Returns:
        Structured meeting output with summary, email draft, and S3 key.
    """
    if agent is None:
        agent = create_legal_advisor_agent()

    prompt = _MEETING_PROMPT_TEMPLATE.format(
        matter_id=meeting_input.matter_id,
        client_code=meeting_input.client_code,
        lawyer_name=meeting_input.lawyer_name,
        client_name=meeting_input.client_name,
        meeting_date=meeting_input.meeting_date.isoformat(),
        jurisdiction=meeting_input.jurisdiction or "Not specified",
        topic_tags=", ".join(meeting_input.topic_tags) if meeting_input.topic_tags else "General",
        transcript_or_notes=meeting_input.transcript_or_notes,
        lawyer_id=meeting_input.lawyer_id,
    )

    response = agent(prompt)
    return _parse_meeting_output(str(response))


def _parse_meeting_output(response_text: str) -> MeetingOutput:
    """Parse agent response into structured MeetingOutput."""
    # Extract JSON from response (agent may wrap with explanation text)
    start = response_text.find("{")
    end = response_text.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("Agent response did not contain valid JSON")

    json_str = response_text[start:end]
    data = json.loads(json_str)

    return MeetingOutput(
        meeting_summary=data.get("meeting_summary", ""),
        agreed_actions=data.get("agreed_actions", []),
        deadlines=data.get("deadlines", []),
        open_questions=data.get("open_questions", []),
        email_subject=data.get("email_subject", ""),
        email_body_text=data.get("email_body_text", ""),
        email_body_html=data.get("email_body_html", ""),
        s3_summary_key=data.get("s3_summary_key", ""),
    )
