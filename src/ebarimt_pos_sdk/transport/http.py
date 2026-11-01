from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Literal, TypeAlias

import httpx

from .._redaction import redact_url
from ..errors import (
    PosApiTransportError,
)

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@dataclass(frozen=True)
class HttpRequestResponse:
    request: httpx.Request
    response: httpx.Response

    def as_tuple(self) -> tuple[httpx.Request, httpx.Response]:
        return (self.request, self.response)


def build_transport_error(
    request: httpx.Request,
    exc: httpx.HTTPError,
) -> PosApiTransportError:
    """Build Pos Api Transport layer error."""
    return PosApiTransportError(
        f"Transport error for {request.method} {redact_url(request.url)}: {exc}",
        request=request,
    )


def parse_retry_after(value: str | None, *, now: datetime | None = None) -> float | None:
    """Parse a ``Retry-After`` header (RFC 9110 §10.2.3) into seconds.

    Accepts the delta-seconds form (``"120"``) and the HTTP-date form
    (``"Wed, 21 Oct 2026 07:28:00 GMT"``). Returns ``None`` for a missing or
    unparseable value so the caller falls back to its own backoff. A date in
    the past yields ``0.0``.
    """
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.isdigit():
        return float(text)
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    current = now if now is not None else datetime.now(timezone.utc)
    return max((when - current).total_seconds(), 0.0)


def retry_after_from(response: httpx.Response) -> float | None:
    """Convenience: ``parse_retry_after`` on a response's header."""
    return parse_retry_after(response.headers.get("Retry-After"))


PrimitiveData = str | int | float | bool | None

QueryParamTypes: TypeAlias = (
    httpx.QueryParams
    | Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
    | list[tuple[str, PrimitiveData]]
    | tuple[tuple[str, PrimitiveData], ...]
    | str
)
HeaderTypes: TypeAlias = (
    httpx.Headers
    | Mapping[str, str]
    | Mapping[bytes, bytes]
    | Sequence[tuple[str, str]]
    | Sequence[tuple[bytes, bytes]]
)
