"""Tests for meeting summary API endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from kao_legal.agents.meeting_summary_workflow import MeetingOutput
from kao_legal.api.middleware.auth import verify_cognito_token


@pytest.fixture
def client(set_test_env):
    from kao_legal.api.app import create_app

    app = create_app()

    # Override auth dependency so tests don't hit real Cognito
    async def mock_auth():
        return {"sub": "user-123", "email": "lawyer@example.com"}

    app.dependency_overrides[verify_cognito_token] = mock_auth
    return TestClient(app)


def test_meeting_summary_no_auth_header():
    """Test that endpoint rejects requests with no Authorization header."""
    from kao_legal.api.app import create_app

    app = create_app()
    c = TestClient(app, raise_server_exceptions=False)

    response = c.post(
        "/api/v1/meeting/summary",
        json={
            "transcript_or_notes": "x" * 50,
            "lawyer_name": "Jane",
            "client_code": "CLI001",
            "client_name": "John",
            "matter_id": "MAT001",
            "meeting_date": "2026-04-20T10:00:00",
        },
    )
    assert response.status_code in (401, 403)


@patch("kao_legal.api.routes.meeting.deduct_credits")
@patch("kao_legal.api.routes.meeting.create_legal_advisor_agent")
@patch("kao_legal.api.routes.meeting.run_meeting_summary")
def test_meeting_summary_success(mock_run, mock_create_agent, mock_deduct, client):
    """Test successful meeting summary creation."""
    mock_deduct.return_value = 90
    mock_run.return_value = MeetingOutput(
        meeting_summary="We discussed the contract.",
        agreed_actions=["File documents"],
        deadlines=["March 15"],
        open_questions=["Confirm payment?"],
        email_subject="Meeting Summary — Matter MAT001",
        email_body_text="Dear Client...",
        email_body_html="<p>Dear Client...</p>",
        s3_summary_key="meeting_summary/user-123/MAT001/2026.json",
    )

    response = client.post(
        "/api/v1/meeting/summary",
        headers={"Authorization": "Bearer test-token"},
        json={
            "transcript_or_notes": "x" * 50,
            "lawyer_name": "Jane",
            "client_code": "CLI001",
            "client_name": "John",
            "matter_id": "MAT001",
            "meeting_date": "2026-04-20T10:00:00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["meeting_summary"] == "We discussed the contract."
    assert data["credits_consumed"] == 10


@patch("kao_legal.api.routes.meeting.deduct_credits")
def test_meeting_summary_insufficient_credits(mock_deduct, client):
    """Test that insufficient credits returns 402."""
    from kao_legal.api.routes.credits import InsufficientCreditsError

    mock_deduct.side_effect = InsufficientCreditsError("user-123", 10)

    response = client.post(
        "/api/v1/meeting/summary",
        headers={"Authorization": "Bearer test-token"},
        json={
            "transcript_or_notes": "x" * 50,
            "lawyer_name": "Jane",
            "client_code": "CLI001",
            "client_name": "John",
            "matter_id": "MAT001",
            "meeting_date": "2026-04-20T10:00:00",
        },
    )

    assert response.status_code == 402
