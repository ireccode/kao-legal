"""Tests for meeting summary workflow."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from kao_legal.agents.meeting_summary_workflow import (
    MeetingInput,
    MeetingOutput,
    _parse_meeting_output,
    run_meeting_summary,
)


def test_parse_meeting_output_valid_json():
    """Test parsing valid JSON from agent response."""
    response = """
    Here is the result:
    {
        "meeting_summary": "We discussed the property purchase.",
        "agreed_actions": ["Review contract", "File documents"],
        "deadlines": ["March 15, 2026"],
        "open_questions": ["Confirm deposit amount?"],
        "email_subject": "Meeting Summary — Matter MAT001",
        "email_body_text": "Dear Client...",
        "email_body_html": "<p>Dear Client...</p>",
        "s3_summary_key": "meeting_summary/lawyer1/MAT001/2026-04-20.json"
    }
    """

    output = _parse_meeting_output(response)

    assert output.meeting_summary == "We discussed the property purchase."
    assert len(output.agreed_actions) == 2
    assert output.deadlines == ["March 15, 2026"]
    assert "Confirm deposit amount?" in output.open_questions
    assert "MAT001" in output.email_subject


def test_parse_meeting_output_invalid_json():
    """Test that invalid JSON raises ValueError."""
    with pytest.raises(ValueError, match="valid JSON"):
        _parse_meeting_output("No JSON here")


def test_run_meeting_summary_calls_agent():
    """Test that run_meeting_summary calls the agent with the right prompt."""
    mock_agent = MagicMock()
    mock_agent.return_value = MagicMock(
        __str__=lambda self: (
            '{"meeting_summary": "test", "agreed_actions": [], '
            '"deadlines": [], "open_questions": [], "email_subject": "test", '
            '"email_body_text": "text", "email_body_html": "<p>text</p>", '
            '"s3_summary_key": "key/path.json"}'
        )
    )

    meeting_input = MeetingInput(
        transcript_or_notes="Client agreed to buy property",
        lawyer_id="lawyer1",
        lawyer_name="Jane Doe",
        client_code="CLI001",
        client_name="John Smith",
        matter_id="MAT001",
        meeting_date=datetime(2026, 4, 20),
        jurisdiction="NSW",
    )

    output = run_meeting_summary(meeting_input, agent=mock_agent)

    mock_agent.assert_called_once()
    assert isinstance(output, MeetingOutput)
    assert output.meeting_summary == "test"
