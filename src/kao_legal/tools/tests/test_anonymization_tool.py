"""Tests for anonymization tool."""

import json

import boto3
from moto import mock_aws

from kao_legal.tools.anonymization_tool import (
    _chunk_text,
    _replace_entities,
    anonymize_document,
)


def test_chunk_text():
    """Test text chunking at UTF-8 boundaries."""
    text = "Hello, World! " * 500
    chunks = _chunk_text(text, 100)

    for chunk in chunks:
        assert len(chunk.encode("utf-8")) <= 100


def test_replace_entities():
    """Test entity replacement maintains text integrity."""
    text = "John Smith lives in New York"
    entities = [
        {"BeginOffset": 0, "EndOffset": 10, "Type": "NAME"},
        {"BeginOffset": 20, "EndOffset": 28, "Type": "ADDRESS"},
    ]

    mapping: dict[str, str] = {}
    result, counters = _replace_entities(text, entities, mapping, {}, "doc1")

    assert "NAME_01" in result
    assert "ADDRESS_01" in result
    assert "John Smith" not in result
    assert "New York" not in result


@mock_aws
def test_anonymize_document_stores_mapping():
    """Test anonymization stores mapping in S3."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="pii-mappings")

    text = "Short text for testing"
    result = anonymize_document(text, document_id="doc123")

    # Mapping key should be created
    response = s3.get_object(Bucket="pii-mappings", Key="mappings/doc123.json")
    mapping = json.loads(response["Body"].read())
    assert isinstance(mapping, dict)
    assert isinstance(result, str)
