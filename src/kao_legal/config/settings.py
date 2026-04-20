"""Application settings and configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # AWS Configuration
    aws_region: str = "us-east-1"

    # Bedrock
    bedrock_model_id: str = "us.anthropic.claude-sonnet-4-6-v1:0"
    bedrock_region: str = "us-east-1"

    # S3 Buckets
    s3_raw_documents_bucket: str
    s3_anonymized_bucket: str
    s3_summaries_bucket: str
    s3_pii_mapping_bucket: str

    # DynamoDB Tables
    dynamodb_users_table: str = "kao-legal-users"
    dynamodb_credits_table: str = "kao-legal-credits"
    dynamodb_audit_table: str = "kao-legal-audit"

    # Cognito
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_region: str = "us-east-1"

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str
    credits_per_dollar: int = 100

    # LangFuse (Optional)
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Application
    log_level: str = "INFO"
    environment: str = "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached Settings instance."""
    return Settings()
