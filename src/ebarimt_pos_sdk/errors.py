from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class HttpRequestContext:
    method: str
    url: str
    headers: Mapping[str, str] | None = None


@dataclass(frozen=True)
class HttpResponseContext:
    status_code: int
    headers: Mapping[str, str]
    body_text: str | None = None
    json: Any | None = None


class PosApiError(Exception):
    """Base error for the SDK."""


class PosApiTransportError(PosApiError):
    """Network / timeout / DNS / TLS errors."""


class PosApiDecodeError(PosApiError):
    """Response body was not valid JSON when JSON was expected."""


class PosApiValidationError(PosApiError):
    """Pydantic validation errors (request or response)."""


class PosApiHttpError(PosApiError):
    """Non-2xx response from server."""

    def __init__(
        self,
        message: str,
        request: HttpRequestContext,
        response: HttpResponseContext,
    ) -> None:
        super().__init__(message)
        self.request = request
        self.response = response
