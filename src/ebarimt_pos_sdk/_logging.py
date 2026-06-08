"""Single home for transport log emission.

All request/response/retry log lines flow through this module so the format,
levels, redaction, and structured ``extra`` fields live in one place and the
sync/async transports cannot drift. Every helper is **best-effort**: a logging
failure (e.g. a formatting bug) must never propagate into a live request such
as a receipt issuance.

Emitted records are *metadata only* — method, redacted URL, status,
``duration_ms``, ``request_id``, ``attempt``. Headers and bodies are never
logged. The ``extra`` keys are chosen to avoid colliding with reserved
``logging.LogRecord`` attributes.
"""

from __future__ import annotations

import logging
from uuid import uuid4

import httpx

from ._redaction import redact_url


def new_request_id() -> str:
    """Short correlation id, generated once per logical request and shared
    across its retry attempts."""
    return uuid4().hex[:8]


def log_request(logger: logging.Logger, request: httpx.Request, request_id: str) -> None:
    """DEBUG line emitted just before an attempt is sent."""
    if not logger.isEnabledFor(logging.DEBUG):
        return
    try:
        logger.debug(
            "→ %s %s [%s]",
            request.method,
            redact_url(request.url),
            request_id,
            extra={
                "request_id": request_id,
                "http_method": request.method,
            },
        )
    except Exception:  # pragma: no cover - logging must never break a request
        pass


def log_response(
    logger: logging.Logger,
    response: httpx.Response,
    request_id: str,
    duration_ms: float,
) -> None:
    """DEBUG line emitted when an attempt returns a response."""
    if not logger.isEnabledFor(logging.DEBUG):
        return
    try:
        logger.debug(
            "← %s in %.0fms [%s]",
            response.status_code,
            duration_ms,
            request_id,
            extra={
                "request_id": request_id,
                "http_status": response.status_code,
                "duration_ms": round(duration_ms, 1),
            },
        )
    except Exception:  # pragma: no cover - logging must never break a request
        pass


def log_retry(
    logger: logging.Logger,
    request_id: str,
    attempt: int,
    max_retries: int,
    reason: str,
    sleep_s: float,
) -> None:
    """WARNING line emitted before backing off for a retry. ``attempt`` is the
    1-based number of the attempt that just failed."""
    if not logger.isEnabledFor(logging.WARNING):
        return
    try:
        logger.warning(
            "retry %d/%d after %s, sleeping %.2fs [%s]",
            attempt,
            max_retries,
            reason,
            sleep_s,
            request_id,
            extra={
                "request_id": request_id,
                "attempt": attempt,
            },
        )
    except Exception:  # pragma: no cover - logging must never break a request
        pass
