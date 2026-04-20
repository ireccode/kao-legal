"""Tests for email draft tool."""

from kao_legal.tools.email_draft_tool import format_email_draft


def test_format_email_draft():
    """Test email draft formatting."""
    result = format_email_draft(
        meeting_summary="We discussed the property purchase agreement.",
        agreed_actions=["Review documents", "Prepare draft"],
        deadlines=["March 15, 2026"],
        open_questions=["Client signature date?"],
        lawyer_name="Jane Doe",
        client_name="John Smith",
        matter_id="MAT001",
        jurisdiction="NSW",
    )

    assert "subject" in result
    assert "body_text" in result
    assert "body_html" in result

    assert "Dear John Smith" in result["body_text"]
    assert "Jane Doe" in result["body_text"]
    assert "MAT001" in result["subject"]
    assert "Review documents" in result["body_text"]
    assert "March 15, 2026" in result["body_text"]
    assert "NSW" in result["body_text"]


def test_email_draft_html_rendering():
    """Test HTML body is properly formatted."""
    result = format_email_draft(
        meeting_summary="Summary & notes",  # & triggers HTML escaping
        agreed_actions=[],
        deadlines=[],
        open_questions=[],
        lawyer_name="Jane",
        client_name="John",
        matter_id="M1",
    )

    html = result["body_html"]
    assert "<br>" in html
    assert "&amp;" in html  # & is HTML-escaped to &amp;
