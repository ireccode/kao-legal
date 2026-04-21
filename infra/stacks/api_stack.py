"""API infrastructure: Lambda function with FastAPI via Mangum."""

from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import (
    aws_apigateway as apigw,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from constructs import Construct


class ApiStack(Stack):
    """API Gateway + Lambda for Kao Legal REST API."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_vars: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api_function = lambda_.DockerImageFunction(
            self,
            "ApiFunction",
            code=lambda_.DockerImageCode.from_image_asset(
                "..",
                file="Dockerfile.api",
                exclude=["infra/cdk.out", "infra/.venv", ".venv", ".git", "frontend", "node_modules", "**/node_modules", "**/.venv"],
            ),
            architecture=lambda_.Architecture.ARM_64,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment=env_vars,
        )

        from aws_cdk import aws_iam as iam
        self.api_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=["*"],
            )
        )
        self.api_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["comprehend:DetectPiiEntities"],
                resources=["*"],
            )
        )

        self.api = apigw.LambdaRestApi(
            self,
            "Api",
            handler=self.api_function,
            rest_api_name="kao-legal-api",
            proxy=True,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
        )
