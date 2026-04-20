"""Meeting notes normalization and segmentation tool."""

from strands import tool


@tool
def normalize_meeting_notes(
    transcript_or_notes: str,
    meeting_date: str,
) -> str:
    """
    Normalize and clean meeting transcript or notes for structured extraction.

    Performs basic text normalization: removes extra whitespace, normalizes
    line breaks, and ensures consistent formatting for downstream processing.

    Args:
        transcript_or_notes: Raw meeting transcript or handwritten notes.
        meeting_date: Date of the meeting (ISO format or natural language).

    Returns:
        Cleaned and normalized meeting text ready for agent processing.
    """
    # Normalize whitespace
    lines = transcript_or_notes.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    normalized = "\n".join(cleaned_lines)

    # Add meeting context header
    header = f"Meeting Date: {meeting_date}\n\n"
    return header + normalized
