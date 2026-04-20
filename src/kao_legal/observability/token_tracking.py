"""Token usage tracking for Bedrock requests."""

from datetime import UTC, datetime

import boto3

from kao_legal.config.settings import get_settings


def record_token_usage(
    lawyer_id: str,
    workflow_type: str,
    matter_id: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """
    Record Bedrock token usage in DynamoDB audit table.

    Args:
        lawyer_id: Authenticated lawyer's ID.
        workflow_type: Either 'meeting_summary' or 'document_intake'.
        matter_id: Matter reference number.
        input_tokens: Number of input tokens consumed.
        output_tokens: Number of output tokens generated.
    """
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.dynamodb_audit_table)

    timestamp = datetime.now(UTC).isoformat()
    total_tokens = input_tokens + output_tokens

    table.put_item(
        Item={
            "audit_id": f"tokens#{lawyer_id}#{timestamp}",
            "lawyer_id": lawyer_id,
            "workflow_type": workflow_type,
            "matter_id": matter_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "timestamp": timestamp,
            "record_type": "token_usage",
        }
    )
