import hashlib
import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

log = logging.getLogger("terravant.rate_limit")

_hits: dict[str, deque] = defaultdict(deque)
_redis_client: Redis | None = None

_WINDOW_MS = 60_000

_SLIDING_WINDOW_SCRIPT = """
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local cutoff = now - window

redis.call("ZREMRANGEBYSCORE", KEYS[1], "-inf", cutoff)

local count = redis.call("ZCARD", KEYS[1])
if count >= limit then
    return 0
end

redis.call("ZADD", KEYS[1], now, member)
redis.call("PEXPIRE", KEYS[1], window + 1000)
return 1
"""


def initialize_rate_limiter() -> None:
    """Connect to Redis and verify availability during application startup."""
    global _redis_client

    settings = get_settings()
    if not settings.REDIS_URL:
        return

    client = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )

    try:
        client.ping()
    except RedisError as exc:
        client.close()
        if getattr(settings, 'is_prod', False):
            raise RuntimeError("Redis is required but unavailable") from exc
        log.warning("Redis unavailable; using in-memory development limiter")
        return

    _redis_client = client
    log.info("Redis-backed authentication rate limiter enabled")


def close_rate_limiter() -> None:
    """Close the Redis connection during application shutdown."""
    global _redis_client

    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None



def rate_limiter_ready() -> bool:
    """Report whether the configured production rate limiter is reachable."""
    settings = get_settings()

    if _redis_client is None:
        return not getattr(settings, "is_prod", False)

    try:
        return bool(_redis_client.ping())
    except RedisError:
        log.exception("Redis readiness check failed")
        return False


def _memory_rate_limit(key: str, limit: int) -> None:
    now = time.monotonic()
    hits = _hits[key]

    while hits and now - hits[0] > 60:
        hits.popleft()

    if len(hits) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again in a minute.",
        )

    hits.append(now)


def auth_rate_limit(request: Request) -> None:
    """Apply an atomic shared Redis limit, or a development-only local fallback."""
    settings = get_settings()
    limit = settings.RATE_LIMIT_AUTH_PER_MIN
    host = request.client.host if request.client else "unknown"
    raw_key = f"{host}:{request.url.path}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    if _redis_client is not None:
        try:
            allowed = _redis_client.eval(
                _SLIDING_WINDOW_SCRIPT,
                1,
                f"terravant:rate-limit:auth:{key_hash}",
                int(time.time() * 1000),
                _WINDOW_MS,
                limit,
                uuid.uuid4().hex,
            )
        except RedisError as exc:
            if getattr(settings, 'is_prod', False):
                log.exception("Redis rate limiter unavailable")
                raise HTTPException(
                    status_code=503,
                    detail="Authentication service temporarily unavailable.",
                ) from exc
            log.warning("Redis request failed; using development fallback")
        else:
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Try again in a minute.",
                )
            return

    elif getattr(settings, 'is_prod', False):
        raise HTTPException(
            status_code=503,
            detail="Authentication rate limiter unavailable.",
        )

    _memory_rate_limit(key_hash, limit)

