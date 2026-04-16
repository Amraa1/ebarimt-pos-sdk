"""Ebarimt Pos API sdk errors."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from pydantic import ValidationError

_SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
    }
)
_SENSITIVE_QUERY_PARAMS = frozenset(
    {
        "access_token",
        "refresh_token",
        "token",
        "id_token",
        "code",
        "client_secret",
    }
)


def _redact_url(url: httpx.URL) -> str:
    """Strip token-bearing query params and any URL fragment from a URL."""
    parts = urlsplit(str(url))
    if not parts.query and not parts.fragment:
        return str(url)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    redacted = [(k, "***" if k.lower() in _SENSITIVE_QUERY_PARAMS else v) for k, v in pairs]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(redacted), ""))


class PosApiError(Exception):
    """Base error for the SDK."""

    def __init__(
        self,
        message: str,
        *,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.request = request
        self.response = response
        self.cause = cause

    @staticmethod
    def _safe_request_str(request: httpx.Request | None) -> str:
        """Return a string representation of the request with sensitive data redacted."""
        if request is None:
            return "None"
        safe_headers = {
            k: "***" if k.lower() in _SENSITIVE_HEADERS else v for k, v in request.headers.items()
        }
        safe_url = _redact_url(request.url)
        return f"{request.method} {safe_url} headers={safe_headers}"

    def __str__(self) -> str:
        lines = [
            f"Message: {self.message}",
            f"Request: {self._safe_request_str(self.request)}",
            f"Response: {self.response}",
            f"Cause: {self.cause}",
        ]

        return "\n".join(lines)


class PosApiTransportError(PosApiError):
    """Network / timeout / DNS / TLS errors."""


class PosApiDecodeError(PosApiError):
    """Response body was not valid JSON when JSON was expected."""


class PosApiValidationError(PosApiError):
    """Pydantic validation errors (request or response)."""

    def __init__(
        self,
        *,
        stage: Literal["request", "response"],
        model: type | str,
        validation_error: ValidationError,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        self.stage = stage
        self.model = model if isinstance(model, str) else model.__name__
        self.validation_error = validation_error

        message = f"Validation failed during {stage} for model '{self.model}'"

        super().__init__(
            message,
            request=request,
            response=response,
            cause=validation_error,
        )

    @property
    def errors(self) -> list:
        """Return Pydantic-style validation errors."""
        return self.validation_error.errors()

    def __str__(self) -> str:
        lines = [self.message]

        for err in self.errors:
            loc = ".".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "")
            typ = err.get("type", "")
            lines.append(f"  - {loc}: {msg} ({typ})")

        return "\n".join(lines)


class PosApiHttpError(PosApiError):
    """Non-2xx response from server."""

    def __init__(
        self,
        *,
        status: str | int | None = None,
        message: str,
        date: datetime | None = None,
        request: httpx.Request,
        response: httpx.Response,
        cause: Exception | None = None,
    ) -> None:
        self.status = status
        self.date = date
        lines = [
            f"HTTP {response.status_code}",
            f"Status: {self.status}",
            f"Message: {message}",
            f"Date: {self.date}",
        ]

        super().__init__("\n".join(lines), request=request, response=response, cause=cause)


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
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message, request=request, response=response)
        self.status = status
        self.code = code
