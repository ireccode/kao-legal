"""Authentication infrastructure: Cognito User Pool."""

from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import (
    aws_cognito as cognito,
)
from constructs import Construct


class AuthStack(Stack):
    """Cognito User Pool for Kao Legal authentication."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        credits_table_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name="kao-legal-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7),
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=_get_removal_policy(),
        )

        self.user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=self.user_pool,
            auth_flows=cognito.AuthFlow(
                user_srp=True,
                user_password=True,
            ),
            generate_secret=False,
        )

        # Outputs for use in other stacks and frontend
        self.user_pool_id = self.user_pool.user_pool_id
        self.client_id = self.user_pool_client.user_pool_client_id


def _get_removal_policy():
    from aws_cdk import RemovalPolicy

    return RemovalPolicy.RETAIN
