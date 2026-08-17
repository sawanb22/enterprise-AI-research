import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .dependencies import get_current_user, quota_service
from .schemas import AuthenticatedUser, UserProfileOut, UserQuotaOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserProfileOut)
def get_current_user_profile(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve current authenticated user profile and active quota statistics."""
    quota = quota_service.get_quota_status(user.id, db)
    return UserProfileOut(user=user, quota=quota)


@router.get("/quota", response_model=UserQuotaOut)
def get_user_quota(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve active user lifetime quota usage and remaining allowance."""
    return quota_service.get_quota_status(user.id, db)
