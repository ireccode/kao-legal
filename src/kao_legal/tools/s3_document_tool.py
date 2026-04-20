"""S3 document fetching and parsing tool."""

import io

import boto3
from strands import tool

from kao_legal.config.settings import get_settings

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".eml"}


@tool
def fetch_document_from_s3(
    s3_key: str,
    bucket_name: str | None = None,
) -> str:
    """
    Fetch a document from S3 and return its text content.

    Supports PDF, DOCX, TXT, and EML file formats. Extracts text
    and returns as plain text suitable for AI processing.

    Args:
        s3_key: The S3 object key for the document.
        bucket_name: Optional bucket override; defaults to configured
            raw documents bucket.

    Returns:
        Extracted plain text content of the document.

    Raises:
        ValueError: If document type is not supported or extraction fails.
    """
    settings = get_settings()
    bucket = bucket_name or settings.s3_raw_documents_bucket

    s3 = boto3.client("s3", region_name=settings.aws_region)
    response = s3.get_object(Bucket=bucket, Key=s3_key)
    body = response["Body"].read()
    content_type = response.get("ContentType", "")

    return _extract_text(body, s3_key, content_type)


def _extract_text(body: bytes, key: str, content_type: str) -> str:
    """Extract text from document bytes based on file type."""
    ext = "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {ext}")

    if ext == ".txt" or "text/plain" in content_type:
        return body.decode("utf-8", errors="replace")

    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(body))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)

    if ext == ".docx":
        from docx import Document

        doc = Document(io.BytesIO(body))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    return body.decode("utf-8", errors="replace")
