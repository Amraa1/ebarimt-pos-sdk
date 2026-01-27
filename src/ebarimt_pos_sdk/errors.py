from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


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

    def __init__(
        self,
        message: str,
        *,
        request: HttpRequestContext | None = None,
        response: HttpResponseContext | None = None,
    ) -> None:
        super().__init__(message)
        self.request = request
        self.response = response


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
        super().__init__(message, request=request, response=response)


class PosApiBusinessError(PosApiError):
    """
    2xx HTTP but domain-level failure indicated by payload fields
    (e.g. {"status":"ERROR", "message":"..."}).
    """

    def __init__(
        self,
        message: str,
        *,
        status: str | None = None,
        code: str | int | None = None,
        request: HttpRequestContext | None = None,
        response: HttpResponseContext | None = None,
    ) -> None:
        super().__init__(message, request=request, response=response)
        self.status = status
        self.code = code
