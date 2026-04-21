"""Agent infrastructure: ECS Fargate for Strands Agent runtime."""

from aws_cdk import (
    Stack,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_ecs as ecs,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_logs as logs,
)
from constructs import Construct


class AgentStack(Stack):
    """ECS Fargate cluster for running Strands Agents."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_vars: dict,
        raw_docs_bucket_arn: str,
        anonymized_bucket_arn: str,
        summaries_bucket_arn: str,
        pii_mapping_bucket_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "AgentVpc", max_azs=2)

        ecs.Cluster(self, "AgentCluster", vpc=vpc)

        # IAM role for the agent task — Bedrock + S3 (NOT pii-mapping)
        self.agent_task_role = iam.Role(
            self,
            "AgentTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # Bedrock access
        self.agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=["*"],
            )
        )

        # S3 access — raw docs (read), anonymized (read), summaries (write)
        self.agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[
                    f"{raw_docs_bucket_arn}/*",
                    f"{anonymized_bucket_arn}/*",
                ],
            )
        )
        self.agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{summaries_bucket_arn}/*"],
            )
        )

        # EXPLICIT DENY on PII mapping bucket — this is the security hard wall
        self.agent_task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                actions=["s3:*"],
                resources=[
                    pii_mapping_bucket_arn,
                    f"{pii_mapping_bucket_arn}/*",
                ],
            )
        )

        # Comprehend for PII detection
        self.agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["comprehend:DetectPiiEntities"],
                resources=["*"],
            )
        )

        task_definition = ecs.FargateTaskDefinition(
            self,
            "AgentTaskDef",
            task_role=self.agent_task_role,
            cpu=1024,
            memory_limit_mib=2048,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )

        log_group = logs.LogGroup(self, "AgentLogs")

        task_definition.add_container(
            "AgentContainer",
            image=ecs.ContainerImage.from_asset(
                "..",
                file="Dockerfile.agent",
                exclude=["infra/cdk.out", "infra/.venv", ".venv", ".git", "frontend", "node_modules", "**/node_modules", "**/.venv"],
            ),
            environment=env_vars,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="agent",
                log_group=log_group,
            ),
        )
