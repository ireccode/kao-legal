"""Tests for document intake workflow."""

from unittest.mock import MagicMock

import pytest

from kao_legal.agents.document_intake_workflow import (
    DocumentInput,
    DocumentOutput,
    _parse_document_output,
    run_document_intake,
)


def test_parse_document_output_valid_json():
    """Test parsing valid JSON from agent response."""
    response = """
    {
        "document_summaries": [
            {
                "filename": "contract.pdf",
                "summary": "Property purchase agreement.",
                "key_dates": ["Settlement: March 15"],
                "key_terms": ["$500,000 purchase price"]
            }
        ],
        "overall_assessment": "Standard purchase agreement.",
        "flags": [],
        "s3_summary_key": "document_intake/lawyer1/MAT001/2026-04-20.json"
    }
    """

    output = _parse_document_output(response)

    assert len(output.document_summaries) == 1
    assert output.document_summaries[0].filename == "contract.pdf"
    assert output.overall_assessment == "Standard purchase agreement."
    assert output.flags == []


def test_parse_document_output_invalid_json():
    """Test that missing JSON raises ValueError."""
    with pytest.raises(ValueError, match="valid JSON"):
        _parse_document_output("No JSON here at all")


def test_run_document_intake_calls_agent():
    """Test that run_document_intake calls agent with proper prompt."""
    mock_agent = MagicMock()
    mock_agent.return_value = MagicMock(
        __str__=lambda self: (
            '{"document_summaries": [], '
            '"overall_assessment": "test", "flags": [], '
            '"s3_summary_key": "key/path.json"}'
        )
    )

    doc_input = DocumentInput(
        s3_keys=["documents/contract.pdf"],
        lawyer_id="lawyer1",
        client_code="CLI001",
        matter_id="MAT001",
        document_group_id="GROUP001",
    )

    output = run_document_intake(doc_input, agent=mock_agent)

    mock_agent.assert_called_once()
    assert isinstance(output, DocumentOutput)
