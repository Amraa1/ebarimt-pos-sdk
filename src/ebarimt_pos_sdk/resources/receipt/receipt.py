from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ...transport import AsyncTransport, SyncTransport
from ..http import raise_for_status, validate_payload
from .schema import CreateReceiptRequest, CreateReceiptResponse

HeaderTypes = httpx.Headers | Mapping[str, Any]


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
        payload = validate_payload(model=CreateReceiptRequest, payload=payload)

        result = self._sync.send(
            "POST",
            self._path,
            headers=self._build_headers(headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        raise_for_status(*result.as_tuple())

        return CreateReceiptResponse.model_validate(result.response.json())

    async def acreate(
        self,
        payload: CreateReceiptRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateReceiptResponse:
        payload = validate_payload(model=CreateReceiptRequest, payload=payload)

        result = await self._async.send(
            "POST",
            self._path,
            headers=self._build_headers(headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        raise_for_status(*result.as_tuple())

        return CreateReceiptResponse.model_validate(result.response.json())

    def delete(self, payload: dict[str, Any], *, headers: HeaderTypes | None = None): ...
    def adelete(self, payload: dict[str, Any], *, headers: HeaderTypes | None = None): ...
