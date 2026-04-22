"""Application settings and configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = "ap-southeast-2"

    # Bedrock
    bedrock_model_id: str = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_region: str = "ap-southeast-2"

    # S3 Buckets
    s3_raw_documents_bucket: str
    s3_anonymized_bucket: str
    s3_summaries_bucket: str
    s3_pii_mapping_bucket: str

    # DynamoDB Tables
    dynamodb_users_table: str = "kao-legal-users"
    dynamodb_credits_table: str = "kao-legal-credits"
    dynamodb_audit_table: str = "kao-legal-audit"
    dynamodb_jobs_table: str = "kao-legal-jobs"

    # Cognito
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_region: str = "ap-southeast-2"

    # Stripe (optional — not required for core Lambda startup)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    credits_per_dollar: int = 100

    # LangFuse (Optional)
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Application
    log_level: str = "INFO"
    environment: str = "development"
    lambda_function_name: str = ""  # set by Lambda runtime for self-invoke


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached Settings instance."""
    return Settings()  # type: ignore[call-arg]
