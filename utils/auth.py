"""
Auth0 OAuth token verification for YouTube MCP Server.

This module provides Auth0 integration to protect the MCP server from
unauthorized access. It verifies JWT tokens issued by Auth0.
"""

import os
from typing import Optional
import httpx
import jwt
from jwt import DecodeError, InvalidTokenError
from jwt.algorithms import RSAAlgorithm
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
        self._jwks_cache: Optional[dict] = None

    async def _get_jwks(self) -> dict:
        """
        Fetch Auth0's JSON Web Key Set (JWKS) for token verification.

        Returns:
            Dictionary containing Auth0's public signing keys
        """
        if self._jwks_cache is not None:
            return self._jwks_cache

        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url, timeout=10.0)
            response.raise_for_status()
            self._jwks_cache = response.json()
            return self._jwks_cache

    def _get_signing_key(self, jwks: dict, token: str) -> str:
        """
        Extract the correct signing key from JWKS based on token's kid header.

        Args:
            jwks: The JWKS dictionary from Auth0
            token: The JWT token

        Returns:
            PEM-formatted public key string
        """
        # Decode token header without verification to get the kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise ValueError("Token does not have a kid header")

        # Find the matching key in JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PEM format using PyJWT's RSAAlgorithm
                public_key = RSAAlgorithm.from_jwk(key)
                return public_key

        raise ValueError(f"Unable to find matching key for kid: {kid}")

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify Auth0 JWT token and return access information.

        This method:
        1. Fetches Auth0's JWKS using async httpx
        2. Finds the correct signing key based on token's kid header
        3. Decodes and verifies the JWT token signature
        4. Validates token claims (issuer, audience, expiration)
        5. Extracts user information and scopes

        Args:
            token: JWT token string from Auth0 (from Authorization header)

        Returns:
            AccessToken if token is valid, None if invalid
        """
        try:
            # Fetch JWKS from Auth0
            jwks = await self._get_jwks()

            # Get the correct signing key for this token
            signing_key = self._get_signing_key(jwks, token)

            # Decode and verify the JWT token
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
