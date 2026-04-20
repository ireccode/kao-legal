"""Storage infrastructure: S3 buckets, KMS keys, DynamoDB tables."""

from aws_cdk import (
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_kms as kms,
)
from aws_cdk import (
    aws_s3 as s3,
)
from constructs import Construct


class StorageStack(Stack):
    """S3 buckets and DynamoDB tables for Kao Legal."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # KMS key for server-side encryption
        self.encryption_key = kms.Key(
            self,
            "EncryptionKey",
            description="Kao Legal data encryption key",
            enable_key_rotation=True,
        )

        # Raw documents bucket (lawyer uploads)
        self.raw_documents_bucket = s3.Bucket(
            self,
            "RawDocumentsBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.encryption_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.PUT],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=300,
                )
            ],
        )

        # Anonymized documents bucket (agent reads from here)
        self.anonymized_bucket = s3.Bucket(
            self,
            "AnonymizedBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.encryption_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Summaries bucket (agent writes output)
        self.summaries_bucket = s3.Bucket(
            self,
            "SummariesBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.encryption_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # PII mapping bucket — RESTRICTED, agent role denied access
        self.pii_mapping_bucket = s3.Bucket(
            self,
            "PiiMappingBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.encryption_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # DynamoDB: Users table
        self.users_table = dynamodb.Table(
            self,
            "UsersTable",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB: Credits table
        self.credits_table = dynamodb.Table(
            self,
            "CreditsTable",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # DynamoDB: Audit table
        self.audit_table = dynamodb.Table(
            self,
            "AuditTable",
            partition_key=dynamodb.Attribute(
                name="audit_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )
