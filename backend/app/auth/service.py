import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from .models import UserQuota
from .schemas import UserQuotaOut

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when a user attempts to execute a research query beyond their free lifetime allowance."""
    pass


class QuotaService:
    """Manages lifetime research run allowances per user."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def get_or_create_quota(self, user_id: str, db: Session) -> UserQuota:
        """Fetch existing quota or initialize new 5-run pilot allowance for user."""
        quota = db.scalar(select(UserQuota).where(UserQuota.user_id == user_id))
        if not quota:
            quota = UserQuota(
                user_id=user_id,
                total_runs_used=0,
                max_free_runs=self.settings.max_free_messages_per_user,
            )
            db.add(quota)
            db.commit()
            db.refresh(quota)
        return quota

    def consume_quota(self, user_id: str, db: Session) -> UserQuota:
        """
        Atomically verify remaining allowance and increment total_runs_used.
        Raises QuotaExceededError if user has already consumed all free queries.
        """
        quota = self.get_or_create_quota(user_id, db)

        if quota.total_runs_used >= quota.max_free_runs:
            logger.warning("User '%s' exceeded quota (%d/%d)", user_id, quota.total_runs_used, quota.max_free_runs)
            raise QuotaExceededError(
                f"Pilot quota reached: You have used all {quota.max_free_runs} free research inquiries. "
                f"Thank you for evaluating the Enterprise Research Agent prototype!"
            )

        quota.total_runs_used += 1
        db.commit()
        db.refresh(quota)
        logger.info("User '%s' consumed quota: %d/%d used", user_id, quota.total_runs_used, quota.max_free_runs)
        return quota

    def get_quota_status(self, user_id: str, db: Session) -> UserQuotaOut:
        """Return structured quota telemetry for the user."""
        quota = self.get_or_create_quota(user_id, db)
        remaining = max(0, quota.max_free_runs - quota.total_runs_used)
        return UserQuotaOut(
            user_id=quota.user_id,
            total_runs_used=quota.total_runs_used,
            max_free_runs=quota.max_free_runs,
            remaining_runs=remaining,
            is_quota_exhausted=(quota.total_runs_used >= quota.max_free_runs),
        )
