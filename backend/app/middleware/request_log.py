import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger("terravant.request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("x-request-id", str(uuid.uuid4()))
        t0 = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000
        response.headers["x-request-id"] = rid
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "no-referrer"
        log.info("%s %s %s %.1fms rid=%s", request.method, request.url.path, response.status_code, ms, rid)
        return response
