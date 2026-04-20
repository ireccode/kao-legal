"""Root conftest: set required environment variables for tests."""

import pytest

# Set all required env vars before any module import
_TEST_ENV = {
    "AWS_REGION": "us-east-1",
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SECURITY_TOKEN": "testing",
    "AWS_SESSION_TOKEN": "testing",
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-6-v1:0",
    "S3_RAW_DOCUMENTS_BUCKET": "test-raw-docs",
    "S3_ANONYMIZED_BUCKET": "test-anonymized",
    "S3_SUMMARIES_BUCKET": "summaries",
    "S3_PII_MAPPING_BUCKET": "pii-mappings",
    "DYNAMODB_USERS_TABLE": "users",
    "DYNAMODB_CREDITS_TABLE": "credits",
    "DYNAMODB_AUDIT_TABLE": "audit",
    "COGNITO_USER_POOL_ID": "us-east-1_test",
    "COGNITO_CLIENT_ID": "test-client-id",
    "STRIPE_SECRET_KEY": "sk_test_fake",
    "STRIPE_WEBHOOK_SECRET": "whsec_fake",
}


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Apply test environment variables to all tests."""
    for key, value in _TEST_ENV.items():
        monkeypatch.setenv(key, value)

    # Clear lru_cache on settings so the test env is picked up
    from kao_legal.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
