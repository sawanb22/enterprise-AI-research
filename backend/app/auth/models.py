from datetime import datetime
from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from ..models import new_id, utc_now


class UserQuota(Base):
    __tablename__ = "user_quotas"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_quota_user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    total_runs_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_free_runs: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
