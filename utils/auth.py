"""
Auth0 OAuth token verification for YouTube MCP Server.

This module provides Auth0 integration to protect the MCP server from
unauthorized access. It verifies JWT tokens issued by Auth0.
"""

import os
import asyncio
from typing import Optional
import jwt
from jwt import PyJWKClient, DecodeError, InvalidTokenError
from mcp.server.auth.provider import AccessToken, TokenVerifier


class Auth0TokenVerifier(TokenVerifier):
    """
    Verifies OAuth tokens issued by Auth0.

    Uses PyJWKClient for reliable JWKS fetching and key matching.
    Runs sync PyJWKClient code in a thread pool to maintain async compatibility.
    """

    def __init__(self, domain: str, audience: str, algorithms: Optional[list[str]] = None):
        """
        Initialize Auth0 token verifier.

        Args:
            domain: Auth0 domain (e.g., 'your-tenant.us.auth0.com')
            audience: API identifier/audience from Auth0
            algorithms: List of allowed signing algorithms (default: ['RS256'])
        """
        self.domain = domain
        self.audience = audience
        self.algorithms = algorithms or ["RS256"]
        self.jwks_url = f"https://{domain}/.well-known/jwks.json"
        self.issuer = f"https://{domain}/"

    def _verify_token_sync(self, token: str) -> dict:
        """
        Synchronous token verification using PyJWKClient.

        This matches the FastAPI example pattern and runs in a thread pool
        via asyncio.to_thread() to maintain async compatibility with FastMCP.
        """
        # PyJWKClient fetches JWKS and automatically caches keys
        jwks_client = PyJWKClient(self.jwks_url, cache_keys=True)

        # Get the signing key for this token
        # IMPORTANT: Must access .key property from the signing key object
        signing_key = jwks_client.get_signing_key_from_jwt(token).key

        # Decode and verify the JWT
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=self.algorithms,
            audience=self.audience,
            issuer=self.issuer,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iat": True,
                "verify_exp": True,
                "verify_iss": True,
            }
        )

        return payload

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify Auth0 JWT token and return access information.

        This is an async wrapper around the sync PyJWKClient verification.

        Args:
            token: JWT token string from Auth0 (from Authorization header)

        Returns:
            AccessToken if token is valid, None if invalid
        """
        try:
            # Run sync verification in a thread pool to avoid blocking
            payload = await asyncio.to_thread(self._verify_token_sync, token)

            # Extract scopes from token
            scopes = []
            if "scope" in payload:
                scopes = payload["scope"].split()
            elif "permissions" in payload:
                scopes = payload["permissions"]

            # Create and return AccessToken
            return AccessToken(
                token=token,
                scopes=scopes,
                expires_at=payload.get("exp"),
                subject=payload.get("sub"),
                client_id=payload.get("azp") or payload.get("client_id"),
            )

        except (DecodeError, InvalidTokenError) as e:
            print(f"JWT verification failed: {e}")
            return None

        except Exception as e:
            print(f"Token verification error: {e}")
            return None


def create_auth0_verifier() -> Auth0TokenVerifier:
    """
    Factory function to create Auth0TokenVerifier with credentials from environment.

    Required Environment Variables:
        AUTH0_DOMAIN: Your Auth0 tenant domain
        AUTH0_AUDIENCE: Your API identifier

    Returns:
        Configured Auth0TokenVerifier instance

    Raises:
        ValueError: If required environment variables are not set
    """
    domain = os.getenv("AUTH0_DOMAIN")
    audience = os.getenv("AUTH0_AUDIENCE")
    algorithms_str = os.getenv("AUTH0_ALGORITHMS", "RS256")

    if not domain:
        raise ValueError(
            "AUTH0_DOMAIN environment variable is required. "
            "Get it from your Auth0 tenant (e.g., your-tenant.us.auth0.com)"
        )

    if not audience:
        raise ValueError(
            "AUTH0_AUDIENCE environment variable is required. "
            "This is your API identifier from Auth0 dashboard"
        )

    # Parse algorithms (comma-separated string to list)
    algorithms = [alg.strip() for alg in algorithms_str.split(",")]

    return Auth0TokenVerifier(
        domain=domain,
        audience=audience,
        algorithms=algorithms
    )
