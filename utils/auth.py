"""
Auth0 OAuth token verification for YouTube MCP Server.

This module provides Auth0 integration to protect the MCP server from
unauthorized access. It verifies JWT tokens issued by Auth0.
"""

import os
from typing import Optional
import jwt
from jwt import PyJWKClient, DecodeError, InvalidTokenError
from mcp.server.auth.provider import AccessToken, TokenVerifier


class Auth0TokenVerifier(TokenVerifier):
    """
    Verifies OAuth tokens issued by Auth0.

    This verifier:
    1. Fetches Auth0's public keys (JWKS) for signature verification
    2. Validates JWT token signature using RS256 algorithm
    3. Verifies token claims (issuer, audience, expiration)
    4. Returns AccessToken with user information and scopes

    Environment Variables Required:
        AUTH0_DOMAIN: Your Auth0 tenant domain (e.g., your-tenant.us.auth0.com)
        AUTH0_AUDIENCE: Your API identifier from Auth0 dashboard
    """

    def __init__(self, domain: str, audience: str, algorithms: Optional[list[str]] = None):
        """
        Initialize Auth0 token verifier.

        Args:
            domain: Auth0 domain (e.g., 'your-tenant.us.auth0.com')
            audience: API identifier/audience from Auth0 (e.g., 'https://yt-mcp.yourdomain.com/api')
            algorithms: List of allowed signing algorithms (default: ['RS256'])
        """
        self.domain = domain
        self.audience = audience
        self.algorithms = algorithms or ["RS256"]
        self.jwks_url = f"https://{domain}/.well-known/jwks.json"
        self.issuer = f"https://{domain}/"
        # PyJWKClient automatically handles JWKS fetching and caching
        self._jwks_client = PyJWKClient(self.jwks_url, cache_keys=True)

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify Auth0 JWT token and return access information.

        This method:
        1. Uses PyJWKClient to automatically fetch the correct signing key
        2. Decodes and verifies the JWT token signature
        3. Validates token claims (issuer, audience, expiration)
        4. Extracts user information and scopes

        Args:
            token: JWT token string from Auth0 (from Authorization header)

        Returns:
            AccessToken if token is valid, None if invalid

        Example:
            When ChatGPT calls your server:
            Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
                                  ↑ This token gets verified
        """
        try:
            # Get the signing key from Auth0's JWKS
            # PyJWKClient automatically:
            # - Fetches JWKS from Auth0
            # - Finds the key matching the token's 'kid' header
            # - Caches keys for performance
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)

            # Decode and verify the JWT token
            # This automatically verifies:
            # - Signature is valid (using Auth0's public key)
            # - Token hasn't expired
            # - Issuer is Auth0
            # - Audience matches your API
            payload = jwt.decode(
                token,
                signing_key.key,
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

            # Extract scopes from token
            # Auth0 stores scopes as space-separated string
            scopes = []
            if "scope" in payload:
                scopes = payload["scope"].split()
            elif "permissions" in payload:
                # Some Auth0 configurations use "permissions" instead
                scopes = payload["permissions"]

            # Create and return AccessToken
            return AccessToken(
                token=token,
                scopes=scopes,
                expires_at=payload.get("exp"),  # Expiration timestamp
                subject=payload.get("sub"),     # User ID
                client_id=payload.get("azp") or payload.get("client_id"),  # Client ID from token
                # Additional Auth0 claims available in payload:
                # - azp: Authorized party (client_id)
                # - gty: Grant type
                # - permissions: List of permissions
            )

        except (DecodeError, InvalidTokenError) as e:
            # Token is invalid (expired, wrong signature, wrong audience, etc.)
            print(f"JWT verification failed: {e}")
            return None

        except Exception as e:
            # Catch-all for other errors (including JWKS fetch failures)
            print(f"Token verification error: {e}")
            return None


def create_auth0_verifier() -> Auth0TokenVerifier:
    """
    Factory function to create Auth0TokenVerifier with credentials from environment.

    This function reads Auth0 configuration from environment variables and
    creates a configured Auth0TokenVerifier instance.

    Required Environment Variables:
        AUTH0_DOMAIN: Your Auth0 tenant domain
        AUTH0_AUDIENCE: Your API identifier

    Optional Environment Variables:
        AUTH0_ALGORITHMS: Comma-separated list of algorithms (default: RS256)

    Returns:
        Configured Auth0TokenVerifier instance

    Raises:
        ValueError: If required environment variables are not set

    Example:
        In your .env file:
            AUTH0_DOMAIN=your-tenant.us.auth0.com
            AUTH0_AUDIENCE=https://yt-mcp.yourdomain.com/api

        In your code:
            verifier = create_auth0_verifier()
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
            "This is your API identifier from Auth0 dashboard "
            "(e.g., https://yt-mcp.yourdomain.com/api)"
        )

    # Parse algorithms (comma-separated string to list)
    algorithms = [alg.strip() for alg in algorithms_str.split(",")]

    return Auth0TokenVerifier(
        domain=domain,
        audience=audience,
        algorithms=algorithms
    )
