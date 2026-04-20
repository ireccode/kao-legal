"""Email draft formatting tool."""

import html

from strands import tool


@tool
def format_email_draft(
    meeting_summary: str,
    agreed_actions: list[str],
    deadlines: list[str],
    open_questions: list[str],
    lawyer_name: str,
    client_name: str,
    matter_id: str,
    jurisdiction: str = "",
) -> dict:
    """
    Format a structured meeting summary into a professional client email draft.

    Returns subject line, plain text body, and HTML body. Does not generate
    new legal advice — only structures provided information into formal letter.

    Args:
        meeting_summary: Brief narrative summary of the meeting (2-4 sentences).
        agreed_actions: List of explicitly agreed actions/instructions.
        deadlines: List of key dates and deadlines mentioned.
        open_questions: Items requiring client clarification or confirmation.
        lawyer_name: Full name of the lawyer sending the email.
        client_name: Client's name for salutation.
        matter_id: Matter reference number for subject line.
        jurisdiction: Optional jurisdiction for footer disclaimer.

    Returns:
        Dict with keys: subject, body_text, body_html.
    """
    disclaimer = (
        "This email summarizes our meeting and is not formal legal advice"
        f"{f' under {jurisdiction} law' if jurisdiction else ''}. "
        "All instructions are subject to formal written confirmation."
    )

    actions_text = "\n".join(f"  {i + 1}. {action}" for i, action in enumerate(agreed_actions))
    deadlines_text = "\n".join(f"  - {d}" for d in deadlines) if deadlines else "  None noted."
    questions_text = "\n".join(f"  - {q}" for q in open_questions) if open_questions else "  None."

    body_text = f"""Dear {client_name},

Thank you for your time today. Please find below a summary of our meeting and \
the agreed next steps.

MEETING SUMMARY
{meeting_summary}

AGREED ACTIONS AND INSTRUCTIONS
{actions_text}

KEY DATES AND DEADLINES
{deadlines_text}

OPEN QUESTIONS (Require Your Confirmation)
{questions_text}

Please review and confirm the above is an accurate record. If you have any \
corrections or additions, please let me know within 48 hours.

DISCLAIMER: {disclaimer}

Warm regards,
{lawyer_name}
"""

    subject = f"Meeting Summary — Matter {matter_id}"

    return {
        "subject": subject,
        "body_text": body_text,
        "body_html": _text_to_html(body_text),
    }


def _text_to_html(text: str) -> str:
    """Convert plain text to basic HTML with line breaks."""
    escaped = html.escape(text)
    lines = escaped.split("\n")
    return "<br>\n".join(lines)
