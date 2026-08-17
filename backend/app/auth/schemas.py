from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    """Normalized authenticated user payload from verified Supabase session."""
    id: str = Field(..., description="Supabase User UUID")
    email: str = Field(..., description="User Email Address")
    full_name: str | None = Field(None, description="User Full Name if available")
    avatar_url: str | None = Field(None, description="User Avatar URL if available")
    role: str = Field("authenticated", description="User role")


class UserQuotaOut(BaseModel):
    """User lifetime research quota statistics."""
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    total_runs_used: int
    max_free_runs: int
    remaining_runs: int
    is_quota_exhausted: bool


class UserProfileOut(BaseModel):
    """Combined user profile and active quota response."""
    user: AuthenticatedUser
    quota: UserQuotaOut
