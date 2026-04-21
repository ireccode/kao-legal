#!/usr/bin/env python3
"""CDK application entry point."""

import os

import aws_cdk as cdk
from stacks.agent_stack import AgentStack
from stacks.api_stack import ApiStack
from stacks.auth_stack import AuthStack
from stacks.storage_stack import StorageStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-2"),
)

storage = StorageStack(app, "KaoLegalStorage", env=env)

auth = AuthStack(
    app,
    "KaoLegalAuth",
    credits_table_name=storage.credits_table.table_name,
    env=env,
)

shared_env_vars = {
    # AWS_REGION and AWS_DEFAULT_REGION are both reserved by the Lambda runtime.
    # Do NOT set either here — Lambda injects them automatically.
    "BEDROCK_MODEL_ID": "apac.anthropic.claude-3-haiku-20240307-v1:0",
    "S3_RAW_DOCUMENTS_BUCKET": storage.raw_documents_bucket.bucket_name,
    "S3_ANONYMIZED_BUCKET": storage.anonymized_bucket.bucket_name,
    "S3_SUMMARIES_BUCKET": storage.summaries_bucket.bucket_name,
    "S3_PII_MAPPING_BUCKET": storage.pii_mapping_bucket.bucket_name,
    "DYNAMODB_USERS_TABLE": storage.users_table.table_name,
    "DYNAMODB_CREDITS_TABLE": storage.credits_table.table_name,
    "DYNAMODB_AUDIT_TABLE": storage.audit_table.table_name,
    "COGNITO_USER_POOL_ID": auth.user_pool_id,
    "COGNITO_CLIENT_ID": auth.client_id,
    "COGNITO_REGION": os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-2"),
    "BEDROCK_REGION": os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-2"),
    "ENVIRONMENT": "production",
    # TODO: Move Stripe keys to AWS Secrets Manager before going live
    "STRIPE_SECRET_KEY": os.environ.get("STRIPE_SECRET_KEY", ""),
    "STRIPE_WEBHOOK_SECRET": os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
}

api = ApiStack(app, "KaoLegalApi", env_vars=shared_env_vars, env=env)

# Grant API Lambda permissions to DynamoDB and S3
storage.users_table.grant_read_write_data(api.api_function)
storage.credits_table.grant_read_write_data(api.api_function)
storage.audit_table.grant_read_write_data(api.api_function)

storage.raw_documents_bucket.grant_read_write(api.api_function)
storage.anonymized_bucket.grant_read_write(api.api_function)
storage.summaries_bucket.grant_read_write(api.api_function)
storage.pii_mapping_bucket.grant_read_write(api.api_function)

agent = AgentStack(
    app,
    "KaoLegalAgent",
    env_vars=shared_env_vars,
    raw_docs_bucket_arn=storage.raw_documents_bucket.bucket_arn,
    anonymized_bucket_arn=storage.anonymized_bucket.bucket_arn,
    summaries_bucket_arn=storage.summaries_bucket.bucket_arn,
    pii_mapping_bucket_arn=storage.pii_mapping_bucket.bucket_arn,
    env=env,
)

app.synth()
