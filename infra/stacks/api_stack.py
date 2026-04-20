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
                ".",
                file="Dockerfile.api",
            ),
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment=env_vars,
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
