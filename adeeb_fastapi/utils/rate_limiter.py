from fastapi import HTTPException, status
from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter
###


def rate_limit_callback(*args, **kwargs):
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too Many Requests, Try again later.",
    )


DEFAULT_RATE_LIMIT = RateLimiter(
    limiter=Limiter(Rate(1000, Duration.SECOND * 60)), # nothing more than 1000 requests in 1 minute
    callback=rate_limit_callback,
    )

USERS_RATE_LIMIT=RateLimiter(
    limiter=Limiter(Rate(30, Duration.SECOND * 60)), # nothing more than 30 requests in 1 minute
    callback=rate_limit_callback,
    )

