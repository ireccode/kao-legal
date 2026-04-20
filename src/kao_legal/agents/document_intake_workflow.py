"""Document intake workflow orchestration."""

import json
from dataclasses import dataclass

from strands import Agent

from kao_legal.agents.legal_advisor_agent import create_legal_advisor_agent


@dataclass
class DocumentInput:
    """Input for the document intake workflow."""

    s3_keys: list[str]
    lawyer_id: str
    client_code: str
    matter_id: str
    document_group_id: str


@dataclass
class DocumentSummary:
    """Summary for a single document."""

    filename: str
    summary: str
    key_dates: list[str]
    key_terms: list[str]


@dataclass
class DocumentOutput:
    """Output from the document intake workflow."""

    document_summaries: list[DocumentSummary]
    overall_assessment: str
    flags: list[str]
    s3_summary_key: str


_DOCUMENT_PROMPT_TEMPLATE = (
    "Process the following documents and provide a structured intake summary.\n\n"
    "MATTER DETAILS:\n"
    "- Matter ID: {matter_id}\n"
    "- Client: {client_code}\n"
    "- Document Group: {document_group_id}\n\n"
    "DOCUMENTS TO PROCESS:\n"
    "{documents_list}\n\n"
    "REQUIRED STEPS:\n"
    "1. For each document, call fetch_document_from_s3 to retrieve its contents.\n"
    "2. Call anonymize_document on each document text using "
    'document_group_id="{document_group_id}".\n'
    "3. Summarize each anonymized document.\n"
    "4. Identify key dates, terms, and any flags or concerns.\n"
    '5. Call export_summary with lawyer_id="{lawyer_id}", '
    'client_code="{client_code}", matter_id="{matter_id}", '
    'workflow_type="document_intake".\n'
    "6. Return the final structured JSON.\n\n"
    "Return ONLY valid JSON with keys: document_summaries (list of objects with "
    "filename, summary, key_dates, key_terms), overall_assessment, flags, s3_summary_key."
)


def run_document_intake(
    document_input: DocumentInput,
    agent: Agent | None = None,
) -> DocumentOutput:
    """
    Execute the document intake and analysis workflow.

    Args:
        document_input: Document processing request data.
        agent: Optional pre-created agent (creates new one if not provided).

    Returns:
        Structured document output with summaries and S3 key.
    """
    if agent is None:
        agent = create_legal_advisor_agent()

    documents_list = "\n".join(f"- {key}" for key in document_input.s3_keys)

    prompt = _DOCUMENT_PROMPT_TEMPLATE.format(
        matter_id=document_input.matter_id,
        client_code=document_input.client_code,
        document_group_id=document_input.document_group_id,
        documents_list=documents_list,
        lawyer_id=document_input.lawyer_id,
    )

    response = agent(prompt)
    return _parse_document_output(str(response))


def _parse_document_output(response_text: str) -> DocumentOutput:
    """Parse agent response into structured DocumentOutput."""
    start = response_text.find("{")
    end = response_text.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("Agent response did not contain valid JSON")

    json_str = response_text[start:end]
    data = json.loads(json_str)

    summaries = [
        DocumentSummary(
            filename=doc.get("filename", ""),
            summary=doc.get("summary", ""),
            key_dates=doc.get("key_dates", []),
            key_terms=doc.get("key_terms", []),
        )
        for doc in data.get("document_summaries", [])
    ]

    return DocumentOutput(
        document_summaries=summaries,
        overall_assessment=data.get("overall_assessment", ""),
        flags=data.get("flags", []),
        s3_summary_key=data.get("s3_summary_key", ""),
    )
