import logging
import secrets
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings

logger = logging.getLogger(__name__)

# Support both header types
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def verify_api_key(
    header_key: str | None = Security(api_key_header),
    bearer_creds: HTTPAuthorizationCredentials | None = Security(http_bearer),
    settings: Settings = Depends(get_settings),
) -> bool:
    """
    Verify incoming request authentication against configured API_AUTH_KEY.
    If API_AUTH_KEY is not configured (empty or None), allows all requests for local development.
    Uses constant-time comparison to prevent timing attacks.
    """
    expected_key = (settings.api_auth_key or "").strip()
    if not expected_key:
        # Permissive dev mode when no key is configured
        return True

    provided_key = None
    if header_key:
        provided_key = header_key.strip()
    elif bearer_creds and bearer_creds.credentials:
        provided_key = bearer_creds.credentials.strip()

    if not provided_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "Bearer, ApiKey"},
        )

    return True
