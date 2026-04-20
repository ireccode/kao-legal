"""Tests for summary export tool."""

import json

import boto3
from moto import mock_aws

from kao_legal.tools.summary_export_tool import export_summary


@mock_aws
def test_export_summary_stores_in_s3_and_dynamodb():
    """Test that export_summary stores data in S3 and records in DynamoDB."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="summaries")

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="audit",
        KeySchema=[{"AttributeName": "audit_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "audit_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    summary_data = {
        "meeting_summary": "Test summary",
        "agreed_actions": ["Action 1"],
    }

    s3_key = export_summary(
        summary_data=summary_data,
        lawyer_id="lawyer123",
        client_code="CLI001",
        matter_id="MAT001",
        workflow_type="meeting_summary",
    )

    assert "meeting_summary" in s3_key
    response = s3.get_object(Bucket="summaries", Key=s3_key)
    stored_data = json.loads(response["Body"].read())
    assert stored_data == summary_data
