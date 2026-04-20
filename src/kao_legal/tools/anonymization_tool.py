"""PII anonymization tool with secure mapping storage."""

import json

import boto3
from strands import tool

from kao_legal.config.settings import get_settings

# AWS Comprehend PII entity types
PII_ENTITY_TYPES = {
    "NAME",
    "ADDRESS",
    "EMAIL",
    "PHONE",
    "SSN",
    "DATE_TIME",
    "BANK_ACCOUNT_NUMBER",
    "CREDIT_DEBIT_NUMBER",
    "PASSPORT_NUMBER",
    "DRIVER_ID",
    "URL",
}

# AWS Comprehend max 5KB per request; use 4500 bytes to stay safe
MAX_COMPREHEND_BYTES = 4500


@tool
def anonymize_document(text: str, document_id: str) -> str:
    """
    Detect and replace PII entities in document text with anonymized codes.

    Uses AWS Comprehend to detect PII and replaces with stable codes like
    PERSON_01, ADDRESS_01, etc. The PII mapping is stored securely in
    a restricted S3 bucket and never returned or visible to the agent.

    Args:
        text: The raw document text potentially containing PII.
        document_id: Unique identifier used to namespace mapping keys
            and ensure deterministic anonymization within a document.

    Returns:
        Anonymized text with PII replaced by stable codes. The mapping
        between codes and original values is stored securely elsewhere.
    """
    settings = get_settings()
    comprehend = boto3.client("comprehend", region_name=settings.aws_region)

    mapping: dict[str, str] = {}
    anonymized = _anonymize_chunks(text, comprehend, mapping, document_id)
    _store_pii_mapping(document_id, mapping, settings)

    return anonymized


def _anonymize_chunks(
    text: str,
    comprehend,
    mapping: dict[str, str],
    document_id: str,
) -> str:
    """Chunk text, detect PII in each chunk, build global mapping."""
    chunks = _chunk_text(text, MAX_COMPREHEND_BYTES)
    entity_counters: dict[str, int] = {}
    result_parts = []

    offset = 0
    for chunk in chunks:
        entities = _detect_pii_entities(chunk, comprehend)

        # Adjust entity offsets to account for chunk position in original text
        for entity in entities:
            entity["BeginOffset"] += offset
            entity["EndOffset"] += offset

        anonymized_chunk, entity_counters = _replace_entities(
            text,
            entities,
            mapping,
            entity_counters,
            document_id,
        )
        result_parts.append(anonymized_chunk[offset : offset + len(chunk)])
        offset += len(chunk.encode("utf-8"))

    return "".join(result_parts)


def _detect_pii_entities(text: str, comprehend) -> list[dict]:
    """Call AWS Comprehend to detect PII entities."""
    response = comprehend.detect_pii_entities(Text=text, LanguageCode="en")
    return response.get("Entities", [])


def _replace_entities(
    text: str,
    entities: list[dict],
    mapping: dict[str, str],
    counters: dict[str, int],
    document_id: str,
) -> tuple[str, dict[str, int]]:
    """Replace PII entities with stable anonymized codes."""
    # Sort entities by offset descending to replace without shifting indices
    sorted_entities = sorted(
        entities,
        key=lambda e: e["BeginOffset"],
        reverse=True,
    )

    text_list = list(text)

    for entity in sorted_entities:
        pii_value = text[entity["BeginOffset"] : entity["EndOffset"]]
        entity_type = entity["Type"]

        # Stable mapping: same PII value → same code within document
        lookup_key = f"{document_id}:{entity_type}:{pii_value}"

        if lookup_key not in mapping:
            counters[entity_type] = counters.get(entity_type, 0) + 1
            token = f"{entity_type}_{counters[entity_type]:02d}"
            mapping[lookup_key] = token
        else:
            token = mapping[lookup_key]

        # Replace in-place from end to start to avoid index shifting
        text_list[entity["BeginOffset"] : entity["EndOffset"]] = list(token)

    return "".join(text_list), counters


def _chunk_text(text: str, max_bytes: int) -> list[str]:
    """Chunk text at UTF-8 boundaries to stay under max_bytes."""
    chunks = []
    remaining = text

    while remaining:
        # Encode chunk and truncate at max_bytes
        chunk_bytes = remaining[: max_bytes * 2].encode("utf-8")[:max_bytes]

        # Back off until we hit a valid UTF-8 boundary
        while len(chunk_bytes) > 0:
            try:
                chunk_bytes.decode("utf-8")
                break
            except UnicodeDecodeError:
                chunk_bytes = chunk_bytes[:-1]

        if not chunk_bytes:
            break

        decoded_chunk = chunk_bytes.decode("utf-8")
        chunks.append(decoded_chunk)
        remaining = remaining[len(decoded_chunk) :]

    return chunks


def _store_pii_mapping(
    document_id: str,
    mapping: dict[str, str],
    settings,
) -> None:
    """Store PII mapping in restricted S3 bucket (never accessible to agent)."""
    s3 = boto3.client("s3", region_name=settings.aws_region)
    key = f"mappings/{document_id}.json"

    s3.put_object(
        Bucket=settings.s3_pii_mapping_bucket,
        Key=key,
        Body=json.dumps(mapping).encode(),
        ServerSideEncryption="aws:kms",
    )
