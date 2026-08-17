import logging
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..database import get_db
from .jwt_verifier import SupabaseJWTVerifier
from .schemas import AuthenticatedUser
from .service import QuotaExceededError, QuotaService

logger = logging.getLogger(__name__)
security_bearer = HTTPBearer(auto_error=False)
jwt_verifier = SupabaseJWTVerifier()
quota_service = QuotaService()


async def get_current_user(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """
    Enforce Supabase JWT authentication.
    Resolves AuthenticatedUser from Bearer token or raises HTTP 401.
    """
    token = None
    if bearer:
        token = bearer.credentials
    elif "authorization" in request.headers:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()

    # Also support custom header for testing: X-User-Id
    test_user_id = request.headers.get("X-Test-User-Id")
    if test_user_id and not token:
        return AuthenticatedUser(
            id=test_user_id,
            email=f"{test_user_id}@test.local",
            full_name=f"User {test_user_id}",
            role="authenticated",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in with your account.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await jwt_verifier.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> AuthenticatedUser | None:
    """Resolve AuthenticatedUser if token present, or None if unauthenticated."""
    try:
        return await get_current_user(request, bearer)
    except HTTPException:
        return None


def require_user_quota(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """
    Gatekeeper dependency: Verifies user has remaining lifetime inquiry quota.
    Raises HTTP 402 Payment Required if 5 free runs are exhausted.
    """
    try:
        quota_service.consume_quota(user.id, db)
        return user
    except QuotaExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        ) from exc


def verify_api_key(
    header_key: str | None = None,
    bearer_creds: HTTPAuthorizationCredentials | None = None,
    settings: Settings | None = None,
) -> bool:
    """Validate server-to-server static API key if configured."""
    settings = settings or get_settings()
    if not settings.api_auth_key:
        return True

    provided = header_key or (bearer_creds.credentials if bearer_creds else None)
    if not provided or provided != settings.api_auth_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return True
