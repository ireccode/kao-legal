/**
 * Amplify v6 Cognito configuration.
 * MUST be called in a 'use client' component — NOT in Server Components.
 */
import { Amplify } from "aws-amplify";

export function configureAmplify(): void {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
        userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
        loginWith: {
          email: true,
        },
      },
    },
  });
}
