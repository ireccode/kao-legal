"""Legal Advisor Agent using Strands Agents SDK with Amazon Bedrock."""

from pathlib import Path

from strands import Agent
from strands.models import BedrockModel

from kao_legal.config.settings import get_settings
from kao_legal.tools.anonymization_tool import anonymize_document
from kao_legal.tools.email_draft_tool import format_email_draft
from kao_legal.tools.meeting_notes_tool import normalize_meeting_notes
from kao_legal.tools.s3_document_tool import fetch_document_from_s3
from kao_legal.tools.summary_export_tool import export_summary

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "system_prompt.txt").read_text()


def create_legal_advisor_agent() -> Agent:
    """
    Create a configured Legal Advisor Agent instance.

    Creates a new Agent per call — Strands Agent is stateful per session,
    so each API request should get a fresh instance.

    Returns:
        Configured Strands Agent ready for use.
    """
    settings = get_settings()

    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.bedrock_region,
        temperature=0.1,
        max_tokens=4096,
    )

    callbacks = []

    if settings.langfuse_secret_key:
        try:
            from langfuse.callback import CallbackHandler

            callbacks.append(
                CallbackHandler(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host,
                )
            )
        except ImportError:
            pass

    return Agent(
        model=model,
        system_prompt=_SYSTEM_PROMPT,
        tools=[
            fetch_document_from_s3,
            anonymize_document,
            normalize_meeting_notes,
            format_email_draft,
            export_summary,
        ],
        callback_handler=callbacks[0] if callbacks else None,
    )
