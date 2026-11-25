from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.middleware import rate_limit


def make_request():
    return Request({
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "path": "/auth/test",
        "query_string": b"",
        "headers": [],
    })


def setup_limiter(monkeypatch, limit=1):
    rate_limit._hits.clear()
    monkeypatch.setattr(rate_limit, "_redis_client", None)
    monkeypatch.setattr(
        rate_limit,
        "get_settings",
        lambda: SimpleNamespace(RATE_LIMIT_AUTH_PER_MIN=limit, is_prod=False),
    )


def test_auth_rate_limit_blocks_excess_requests(monkeypatch):
    setup_limiter(monkeypatch)
    request = make_request()

    rate_limit.auth_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        rate_limit.auth_rate_limit(request)

    assert exc.value.status_code == 429


def test_auth_rate_limit_resets_after_window(monkeypatch):
    setup_limiter(monkeypatch)
    request = make_request()
    times = iter([100.0, 160.1])
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: next(times))

    rate_limit.auth_rate_limit(request)
    rate_limit.auth_rate_limit(request)


def test_auth_rate_limit_separates_endpoints(monkeypatch):
    setup_limiter(monkeypatch)
    first = make_request()
    second = make_request()
    second.scope["path"] = "/auth/another"

    rate_limit.auth_rate_limit(first)
    rate_limit.auth_rate_limit(second)


class FakeRedis:
    def __init__(self, results=None, ping_result=True, error=None):
        self.results = iter(results or [])
        self.ping_result = ping_result
        self.error = error
        self.calls = []

    def eval(self, *args):
        self.calls.append(args)
        if self.error:
            raise self.error
        return next(self.results)

    def ping(self):
        if self.error:
            raise self.error
        return self.ping_result


def test_redis_rate_limit_blocks_excess_requests(monkeypatch):
    setup_limiter(monkeypatch, limit=1)
    client = FakeRedis(results=[1, 0])
    monkeypatch.setattr(rate_limit, "_redis_client", client)

    rate_limit.auth_rate_limit(make_request())

    with pytest.raises(HTTPException) as exc:
        rate_limit.auth_rate_limit(make_request())

    assert exc.value.status_code == 429
    assert len(client.calls) == 2


def test_production_fails_closed_when_redis_is_unavailable(monkeypatch):
    setup_limiter(monkeypatch)
    monkeypatch.setattr(
        rate_limit,
        "get_settings",
        lambda: SimpleNamespace(RATE_LIMIT_AUTH_PER_MIN=1, is_prod=True),
    )
    monkeypatch.setattr(rate_limit, "_redis_client", None)

    with pytest.raises(HTTPException) as exc:
        rate_limit.auth_rate_limit(make_request())

    assert exc.value.status_code == 503


def test_redis_error_fails_closed_in_production(monkeypatch):
    from redis.exceptions import RedisError

    setup_limiter(monkeypatch)
    monkeypatch.setattr(
        rate_limit,
        "get_settings",
        lambda: SimpleNamespace(RATE_LIMIT_AUTH_PER_MIN=1, is_prod=True),
    )
    monkeypatch.setattr(
        rate_limit,
        "_redis_client",
        FakeRedis(error=RedisError("connection lost")),
    )

    with pytest.raises(HTTPException) as exc:
        rate_limit.auth_rate_limit(make_request())

    assert exc.value.status_code == 503


def test_redis_readiness(monkeypatch):
    setup_limiter(monkeypatch)
    client = FakeRedis(ping_result=True)
    monkeypatch.setattr(rate_limit, "_redis_client", client)

    assert rate_limit.rate_limiter_ready() is True


def test_redis_readiness_fails_when_unavailable(monkeypatch):
    from redis.exceptions import RedisError

    setup_limiter(monkeypatch)
    client = FakeRedis(error=RedisError("connection lost"))
    monkeypatch.setattr(rate_limit, "_redis_client", client)

    assert rate_limit.rate_limiter_ready() is False
