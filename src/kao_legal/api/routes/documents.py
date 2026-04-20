"""Document intake and upload API routes."""

import uuid

import boto3
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from kao_legal.agents.document_intake_workflow import DocumentInput, run_document_intake
from kao_legal.agents.legal_advisor_agent import create_legal_advisor_agent
from kao_legal.api.middleware.auth import verify_cognito_token
from kao_legal.api.routes.credits import (
    CREDITS_PER_DOCUMENT,
    InsufficientCreditsError,
    deduct_credits,
)
from kao_legal.config.settings import get_settings

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

PRESIGNED_URL_EXPIRY_SECONDS = 300


class DocumentIntakeRequest(BaseModel):
    s3_keys: list[str] = Field(..., min_length=1)
    client_code: str
    matter_id: str
    document_group_id: str


class PresignedUploadRequest(BaseModel):
    filename: str
    content_type: str
    matter_id: str


class PresignedUploadResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in_seconds: int


@router.post("/upload-url", response_model=PresignedUploadResponse)
async def get_upload_url(
    request: PresignedUploadRequest,
    claims: dict = Depends(verify_cognito_token),
) -> PresignedUploadResponse:
    """
    Generate a pre-signed S3 URL for direct client upload.

    Client must PUT to the returned URL with matching Content-Type header.
    URL expires in 5 minutes.
    """
    settings = get_settings()
    user_id = claims["sub"]

    file_id = str(uuid.uuid4())
    s3_key = f"uploads/{user_id}/{request.matter_id}/{file_id}/{request.filename}"

    s3 = boto3.client("s3", region_name=settings.aws_region)
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_raw_documents_bucket,
            "Key": s3_key,
            "ContentType": request.content_type,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY_SECONDS,
    )

    return PresignedUploadResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in_seconds=PRESIGNED_URL_EXPIRY_SECONDS,
    )


@router.post("/intake")
async def document_intake(
    request: DocumentIntakeRequest,
    claims: dict = Depends(verify_cognito_token),
) -> dict:
    """
    Run document intake analysis on uploaded S3 documents.

    Deducts credits per document processed.
    """
    lawyer_id = claims["sub"]
    cost = CREDITS_PER_DOCUMENT * len(request.s3_keys)

    try:
        deduct_credits(lawyer_id, cost)
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Need {e.required} credits.",
        ) from e

    agent = create_legal_advisor_agent()
    doc_input = DocumentInput(
        s3_keys=request.s3_keys,
        lawyer_id=lawyer_id,
        client_code=request.client_code,
        matter_id=request.matter_id,
        document_group_id=request.document_group_id,
    )

    output = run_document_intake(doc_input, agent=agent)

    return {
        "document_summaries": [
            {
                "filename": doc.filename,
                "summary": doc.summary,
                "key_dates": doc.key_dates,
                "key_terms": doc.key_terms,
            }
            for doc in output.document_summaries
        ],
        "overall_assessment": output.overall_assessment,
        "flags": output.flags,
        "s3_summary_key": output.s3_summary_key,
        "credits_consumed": cost,
    }
