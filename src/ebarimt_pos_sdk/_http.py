from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

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


def _merge_headers(a: Mapping[str, str] | None, b: Mapping[str, str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    if a:
        out.update(dict(a))
    if b:
        out.update(dict(b))
    return out


def _extract_response_json(r: httpx.Response) -> Any | None:
    """
    Best-effort JSON parse. Returns None if not JSON.
    """
    try:
        # Fast-path: only attempt if content-type hints JSON
        ct = r.headers.get("content-type", "")
        if "json" not in ct.lower():
            return None
        return r.json()
    except Exception:
        return None


def _extract_body_text(r: httpx.Response) -> str | None:
    try:
        # note: may raise for streamed responses, but httpx buffers by default
        return r.text
    except Exception:
        return None


def _raise_http_error(
    method: str,
    url: str,
    req_headers: Mapping[str, str],
    r: httpx.Response,
) -> None:
    json_body = _extract_response_json(r)
    body_text = _extract_body_text(r) if json_body is None else None

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
    method: str,
    url: str,
    req_headers: Mapping[str, str],
    r: httpx.Response,
) -> Any:
    # 204/empty is legal sometimes; treat as None
    if r.status_code == 204 or not r.content:
        return None

    # First try JSON even if content-type is wrong (vendor specs often are)
    try:
        return r.json()
    except Exception as e:
        body_text = _extract_body_text(r)
        raise PosApiDecodeError(
            f"Invalid JSON response for {method} {url}: {e}",
            request=HttpRequestContext(method=method, url=url, headers=req_headers),
            response=HttpResponseContext(
                status_code=r.status_code,
                headers=dict(r.headers),
                body_text=body_text,
                json=None,
            ),
        ) from e


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
                f"Transport error for {method} {url}: {e}",
                request=HttpRequestContext(method=method, url=url, headers=headers),
                response=None,
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
                f"Transport error for {method} {url}: {e}",
                request=HttpRequestContext(method=method, url=url, headers=headers),
                response=None,
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
