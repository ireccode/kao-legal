"""Tests for S3 document tool."""

import boto3
import pytest
from moto import mock_aws

from kao_legal.tools.s3_document_tool import fetch_document_from_s3


@mock_aws
def test_fetch_text_document():
    """Test fetching plain text document from S3."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bucket")
    s3.put_object(Bucket="test-bucket", Key="test.txt", Body=b"Hello, World!")

    result = fetch_document_from_s3("test.txt", bucket_name="test-bucket")
    assert result == "Hello, World!"


@mock_aws
def test_fetch_unsupported_format():
    """Test that unsupported file formats raise ValueError."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bucket")
    s3.put_object(Bucket="test-bucket", Key="test.xyz", Body=b"content")

    with pytest.raises(ValueError, match="Unsupported document type"):
        fetch_document_from_s3("test.xyz", bucket_name="test-bucket")
