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
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

storage = StorageStack(app, "KaoLegalStorage", env=env)

auth = AuthStack(
    app,
    "KaoLegalAuth",
    credits_table_name=storage.credits_table.table_name,
    env=env,
)

shared_env_vars = {
    "AWS_REGION": os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-6-v1:0",
    "S3_RAW_DOCUMENTS_BUCKET": storage.raw_documents_bucket.bucket_name,
    "S3_ANONYMIZED_BUCKET": storage.anonymized_bucket.bucket_name,
    "S3_SUMMARIES_BUCKET": storage.summaries_bucket.bucket_name,
    "S3_PII_MAPPING_BUCKET": storage.pii_mapping_bucket.bucket_name,
    "DYNAMODB_USERS_TABLE": storage.users_table.table_name,
    "DYNAMODB_CREDITS_TABLE": storage.credits_table.table_name,
    "DYNAMODB_AUDIT_TABLE": storage.audit_table.table_name,
    "COGNITO_USER_POOL_ID": auth.user_pool_id,
    "COGNITO_CLIENT_ID": auth.client_id,
}

api = ApiStack(app, "KaoLegalApi", env_vars=shared_env_vars, env=env)

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
