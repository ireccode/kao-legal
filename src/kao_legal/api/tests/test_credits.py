"""Tests for credits routes and utilities."""

import boto3
import pytest
from moto import mock_aws

from kao_legal.api.routes.credits import (
    InsufficientCreditsError,
    deduct_credits,
    get_credit_balance,
)


def _create_credits_table(dynamodb):
    return dynamodb.create_table(
        TableName="credits",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


@mock_aws
def test_deduct_credits_success():
    """Test successful credit deduction."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = _create_credits_table(dynamodb)
    table.put_item(Item={"user_id": "user-123", "credits": 100})

    remaining = deduct_credits("user-123", 10)
    assert remaining == 90


@mock_aws
def test_deduct_credits_insufficient():
    """Test that insufficient credits raises InsufficientCreditsError."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = _create_credits_table(dynamodb)
    table.put_item(Item={"user_id": "user-123", "credits": 5})

    with pytest.raises(InsufficientCreditsError):
        deduct_credits("user-123", 10)


@mock_aws
def test_get_credit_balance():
    """Test fetching credit balance."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = _create_credits_table(dynamodb)
    table.put_item(Item={"user_id": "user-123", "credits": 250})

    balance = get_credit_balance("user-123")
    assert balance == 250


@mock_aws
def test_get_credit_balance_nonexistent_user():
    """Test balance for user with no credits returns 0."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    _create_credits_table(dynamodb)

    balance = get_credit_balance("unknown-user")
    assert balance == 0
