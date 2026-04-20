"""Stripe webhook handler."""

import boto3
import stripe
from fastapi import APIRouter, HTTPException, Request, status

from kao_legal.config.settings import get_settings

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

CREDITS_PER_DOLLAR = 100


@router.post("/stripe")
async def stripe_webhook(request: Request) -> dict:
    """
    Handle Stripe webhook events for credit purchases.

    Verifies webhook signature, processes checkout.session.completed
    events to increment user credits atomically.
    """
    settings = get_settings()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.stripe_webhook_secret,
        )
    except stripe.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook signature",
        ) from e

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_checkout_completed(session, settings)

    return {"status": "ok"}


def _handle_checkout_completed(session: dict, settings) -> None:
    """Process completed checkout — increment user credits."""
    user_id = session.get("metadata", {}).get("user_id")
    if not user_id:
        return

    amount_total = session.get("amount_total", 0)
    dollars = amount_total / 100
    credits_to_add = int(dollars * settings.credits_per_dollar)

    if credits_to_add <= 0:
        return

    # Idempotency key: use Stripe session ID to prevent double-crediting
    session_id = session.get("id", "")

    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.dynamodb_credits_table)

    # Use update expression to atomically add credits
    # Condition prevents processing the same session twice
    from botocore.exceptions import ClientError

    try:
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET credits = if_not_exists(credits, :zero) + :amount, "
            "processed_sessions = list_append("
            "if_not_exists(processed_sessions, :empty_list), :session)",
            ConditionExpression="NOT contains(processed_sessions, :session_id)",
            ExpressionAttributeValues={
                ":amount": credits_to_add,
                ":zero": 0,
                ":session": [session_id],
                ":empty_list": [],
                ":session_id": session_id,
            },
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # Session already processed — idempotent, not an error
            return
        raise
