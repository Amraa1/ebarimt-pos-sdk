from __future__ import annotations

from typing import Any

from ...transport import AsyncTransport, SyncTransport
from ..resource import (
    BaseResource,
    HeaderTypes,
    _build_headers,
    _ensure_http_success,
    _validate_payload,
)
from .schema import (
    CreateReceiptRequest,
    CreateReceiptResponse,
    DeleteReceiptRequest,
    DeleteReceiptResponse,
)

_DEFAULT_HEADERS = {"Accept": "application/json"}


class ReceiptResource(BaseResource):
    def __init__(
        self,
        *,
        sync: SyncTransport,
        async_: AsyncTransport,
        headers: HeaderTypes | None = None,
    ) -> None:
        super().__init__(sync=sync, async_=async_, headers=headers)
        self._path = "/rest/receipt"

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
            headers=_build_headers(self._headers, headers),
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
            headers=_build_headers(self._headers, headers),
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
            headers=_build_headers(self._headers, headers),
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
            headers=_build_headers(self._headers, headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        _ensure_http_success(result.response)

        return DeleteReceiptResponse.model_validate(result.response.json())
