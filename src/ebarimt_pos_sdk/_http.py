from __future__ import annotations

from typing import Any, Mapping, Optional, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .errors import (
    HttpRequestContext,
    HttpResponseContext,
    PosApiDecodeError,
    PosApiHttpError,
    PosApiTransportError,
    PosApiValidationError,
)

T = TypeVar("T", bound=BaseModel)


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _merge_headers(
    a: Optional[Mapping[str, str]], b: Optional[Mapping[str, str]]
) -> dict[str, str]:
    out: dict[str, str] = {}
    if a:
        out.update(dict(a))
    if b:
        out.update(dict(b))
    return out


def _raise_http_error(
    method: str, url: str, req_headers: Mapping[str, str], r: httpx.Response
) -> None:
    body_text: str | None = None
    json_body: Any | None = None
    try:
        body_text = r.text
        # try json best-effort
        json_body = r.json()
    except Exception:
        pass

    raise PosApiHttpError(
        f"HTTP {r.status_code} for {method} {url}",
        request=HttpRequestContext(method=method, url=url, headers=req_headers),
        response=HttpResponseContext(
            status_code=r.status_code,
            headers=dict(r.headers),
            body_text=body_text,
            json=json_body,
        ),
    )


def _parse_json_or_raise(
    method: str, url: str, req_headers: Mapping[str, str], r: httpx.Response
) -> Any:
    try:
        return r.json()
    except Exception as e:
        raise PosApiDecodeError(f"Invalid JSON response for {method} {url}: {e}") from e


def _validate_model(model: type[T], data: Any, *, where: str) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise PosApiValidationError(f"Validation failed ({where}): {e}") from e


class AsyncTransport:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        json_body: Any | None = None,
    ) -> Any:
        try:
            r = await self._client.request(method, url, headers=headers, json=json_body)
        except httpx.HTTPError as e:
            raise PosApiTransportError(
                f"Transport error for {method} {url}: {e}"
            ) from e

        if r.status_code < 200 or r.status_code >= 300:
            _raise_http_error(method, url, headers, r)

        return _parse_json_or_raise(method, url, headers, r)


class SyncTransport:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        json_body: Any | None = None,
    ) -> Any:
        try:
            r = self._client.request(method, url, headers=headers, json=json_body)
        except httpx.HTTPError as e:
            raise PosApiTransportError(
                f"Transport error for {method} {url}: {e}"
            ) from e

        if r.status_code < 200 or r.status_code >= 300:
            _raise_http_error(method, url, headers, r)

        return _parse_json_or_raise(method, url, headers, r)


__all__ = [
    "AsyncTransport",
    "SyncTransport",
    "_join_url",
    "_merge_headers",
    "_validate_model",
]
