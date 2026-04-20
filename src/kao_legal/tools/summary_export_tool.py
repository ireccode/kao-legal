"""Summary export and audit logging tool."""

import json
from datetime import UTC, datetime

import boto3
from strands import tool

from kao_legal.config.settings import get_settings


@tool
def export_summary(
    summary_data: dict,
    lawyer_id: str,
    client_code: str,
    matter_id: str,
    workflow_type: str,
) -> str:
    """
    Persist the agent's structured output to S3 and record audit entry.

    Archives the complete workflow output (meeting summary, document intake,
    etc.) in S3 for retrieval and audit purposes. Records metadata in DynamoDB.

    Args:
        summary_data: The structured JSON summary from the agent.
        lawyer_id: The authenticated lawyer's user ID.
        client_code: Anonymized client identifier.
        matter_id: The matter reference number.
        workflow_type: Either 'meeting_summary' or 'document_intake'.

    Returns:
        S3 key of the stored summary for future retrieval.
    """
    settings = get_settings()
    timestamp = datetime.now(UTC).isoformat()
    s3_key = f"{workflow_type}/{lawyer_id}/{matter_id}/{timestamp}.json"

    s3 = boto3.client("s3", region_name=settings.aws_region)
    s3.put_object(
        Bucket=settings.s3_summaries_bucket,
        Key=s3_key,
        Body=json.dumps(summary_data).encode(),
        ServerSideEncryption="aws:kms",
    )

    _write_audit_record(
        lawyer_id,
        client_code,
        matter_id,
        s3_key,
        workflow_type,
        settings,
    )

    return s3_key


def _write_audit_record(
    lawyer_id: str,
    client_code: str,
    matter_id: str,
    s3_key: str,
    workflow_type: str,
    settings,
) -> None:
    """Write audit trail to DynamoDB."""
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.dynamodb_audit_table)

    timestamp = datetime.now(UTC).isoformat()

    table.put_item(
        Item={
            "audit_id": f"{lawyer_id}#{timestamp}",
            "lawyer_id": lawyer_id,
            "client_code": client_code,
            "matter_id": matter_id,
            "workflow_type": workflow_type,
            "s3_key": s3_key,
            "timestamp": timestamp,
        }
    )
