import time
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter per client IP."""

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> tuple[bool, int, int]:
        """
        Check if request is allowed.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        with self._lock:
            # Clean expired timestamps for this key
            timestamps = self._requests[key]
            valid_timestamps = [t for t in timestamps if t > window_start]

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + window_seconds - current_time))
                self._requests[key] = valid_timestamps
                return False, 0, retry_after

            valid_timestamps.append(current_time)
            self._requests[key] = valid_timestamps
            remaining = max(0, max_requests - len(valid_timestamps))
            return True, remaining, 0

    def reset(self):
        """Clear all rate limit tracking (useful in tests)."""
        with self._lock:
            self._requests.clear()


# Global limiter instance
limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For or socket host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """FastAPI dependency for rate limiting an endpoint."""
    async def dependency(request: Request):
        client_ip = get_client_ip(request)
        key = f"{client_ip}:{request.url.path}"
        allowed, remaining, retry_after = limiter.check(key, max_requests, window_seconds)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s. Please retry in {retry_after}s.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

    return dependency
