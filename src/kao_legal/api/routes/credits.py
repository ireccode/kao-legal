"""Credits management routes and utilities."""

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends

from kao_legal.api.middleware.auth import verify_cognito_token
from kao_legal.config.settings import get_settings

router = APIRouter(prefix="/api/v1/credits", tags=["credits"])

CREDITS_PER_MEETING_SUMMARY = 10
CREDITS_PER_DOCUMENT = 5


class InsufficientCreditsError(Exception):
    """Raised when a user has insufficient credits for an operation."""

    def __init__(self, user_id: str, required: int) -> None:
        self.user_id = user_id
        self.required = required
        super().__init__(f"User {user_id} has insufficient credits (need {required})")


def deduct_credits(user_id: str, amount: int) -> int:
    """
    Atomically deduct credits from user account.

    Uses DynamoDB ConditionExpression to prevent overdraft without
    a read-then-write race condition.

    Args:
        user_id: The authenticated user's ID.
        amount: Number of credits to deduct.

    Returns:
        Remaining credit balance after deduction.

    Raises:
        InsufficientCreditsError: If balance would go below zero.
    """
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.dynamodb_credits_table)

    try:
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET credits = credits - :amount",
            ConditionExpression="credits >= :amount",
            ExpressionAttributeValues={":amount": amount},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["credits"])  # type: ignore[arg-type]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise InsufficientCreditsError(user_id, amount) from e
        raise


def refund_credits(user_id: str, amount: int) -> int:
    """
    Add credits back to user account (refund after a failed operation).

    Args:
        user_id: The authenticated user's ID.
        amount: Number of credits to restore.

    Returns:
        New credit balance after refund.
    """
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.dynamodb_credits_table)

    response = table.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET credits = if_not_exists(credits, :zero) + :amount",
        ExpressionAttributeValues={":amount": amount, ":zero": 0},
        ReturnValues="UPDATED_NEW",
    )
    return int(response["Attributes"]["credits"])  # type: ignore[arg-type]


def get_credit_balance(user_id: str) -> int:
    """Get current credit balance for a user."""
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.dynamodb_credits_table)

    response = table.get_item(Key={"user_id": user_id})
    item = response.get("Item")

    if not item:
        return 0

    return int(item.get("credits", 0))  # type: ignore[arg-type]


@router.get("/")
async def get_credits(
    claims: dict = Depends(verify_cognito_token),
) -> dict:
    """Get current credit balance for authenticated user."""
    user_id = claims["sub"]
    balance = get_credit_balance(user_id)
    return {"user_id": user_id, "credits": balance}
