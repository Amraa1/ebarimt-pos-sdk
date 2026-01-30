# src/ebarimt_pos_sdk/resources/receipt.py
from __future__ import annotations

from abc import abstractmethod
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from ..errors import PosApiHttpError
from ..transport import AsyncTransport, HeaderTypes, SyncTransport

T = TypeVar("T", bound=BaseModel)


class BaseResource:
    def __init__(
        self,
        *,
        sync: SyncTransport,
        async_: AsyncTransport,
        headers: HeaderTypes | None = None,
    ) -> None:
        self._sync = sync
        self._async = async_
        self._headers = headers

    @property
    @abstractmethod
    def _path(self) -> str: ...


def _ensure_http_success(response: httpx.Response) -> httpx.Response:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PosApiHttpError(
            f"HTTP {exc.response.status_code}",
            request=exc.request,
            response=exc.response,
        ) from exc
    return response


def _validate_payload(model: type[T], payload: T | dict[str, Any]) -> T:
    if isinstance(payload, model):
        return payload
    return model.model_validate(payload)


def _build_headers(*headers: HeaderTypes | None) -> httpx.Headers:
    """Merges headers and returns one header.

    Note:
        Highest priority header should be the last.

    Returns:
        httpx.Headers: Merged header.
    """
    out = httpx.Headers()
    for header in headers:
        out.update(header)
    return out


__all__ = ["_ensure_http_success", "_validate_payload", "_build_headers"]
