from __future__ import annotations

from typing import Any

import httpx

from ...transport import AsyncTransport, SyncTransport
from ..resource import HeaderTypes, _ensure_http_success, _validate_payload
from .schema import (
    CreateReceiptRequest,
    CreateReceiptResponse,
    DeleteReceiptRequest,
    DeleteReceiptResponse,
)

_DEFAULT_HEADERS = {"Accept": "application/json"}


class ReceiptResource:
    def __init__(
        self,
        *,
        sync: SyncTransport,
        async_: AsyncTransport,
        headers: HeaderTypes | None = None,
    ) -> None:
        self._sync = sync
        self._async = async_
        self._path = "/rest/receipt"
        self._headers = headers

    def _build_headers(self, headers: HeaderTypes | None) -> httpx.Headers:
        out = httpx.Headers(_DEFAULT_HEADERS)
        if self._headers is not None:
            out.update(self._headers)  # client
        if headers is not None:
            out.update(headers)  # call-level
        return out

    def create(
        self,
        payload: CreateReceiptRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateReceiptResponse:
        payload = _validate_payload(model=CreateReceiptRequest, payload=payload)

        result = self._sync.send(
            "POST",
            self._path,
            headers=self._build_headers(headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        _ensure_http_success(result.response)

        return CreateReceiptResponse.model_validate(result.response.json())

    async def acreate(
        self,
        payload: CreateReceiptRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateReceiptResponse:
        payload = _validate_payload(model=CreateReceiptRequest, payload=payload)

        result = await self._async.send(
            "POST",
            self._path,
            headers=self._build_headers(headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        _ensure_http_success(result.response)

        return CreateReceiptResponse.model_validate(result.response.json())

    def delete(
        self, payload: DeleteReceiptRequest | dict[str, Any], *, headers: HeaderTypes | None = None
    ) -> DeleteReceiptResponse:
        payload = _validate_payload(model=DeleteReceiptRequest, payload=payload)

        result = self._sync.send(
            "POST",
            self._path,
            headers=self._build_headers(headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        _ensure_http_success(result.response)

        return DeleteReceiptResponse.model_validate(result.response.json())

    async def adelete(
        self, payload: DeleteReceiptRequest | dict[str, Any], *, headers: HeaderTypes | None = None
    ) -> DeleteReceiptResponse:
        payload = _validate_payload(model=DeleteReceiptRequest, payload=payload)

        result = await self._async.send(
            "POST",
            self._path,
            headers=self._build_headers(headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        _ensure_http_success(result.response)

        return DeleteReceiptResponse.model_validate(result.response.json())
