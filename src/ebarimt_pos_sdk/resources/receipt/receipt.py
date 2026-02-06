from __future__ import annotations

from typing import Any

from ..resource import BaseResource, HeaderTypes
from .schema import (
    CreateReceiptRequest,
    CreateReceiptResponse,
    DeleteReceiptRequest,
    DeleteReceiptResponse,
)


class ReceiptResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/rest/receipt"

    def create(
        self,
        payload: CreateReceiptRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateReceiptResponse:
        payload = self._validate_payload(model=CreateReceiptRequest, payload=payload)

        result = self._sync.send(
            "POST",
            self._path,
            headers=self._build_headers(self._headers, headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        self._ensure_http_success(result.response)

        return CreateReceiptResponse.model_validate(self._decode_json(result.response))

    async def acreate(
        self,
        payload: CreateReceiptRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateReceiptResponse:
        payload = self._validate_payload(model=CreateReceiptRequest, payload=payload)

        result = await self._async.send(
            "POST",
            self._path,
            headers=self._build_headers(self._headers, headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        self._ensure_http_success(result.response)

        return CreateReceiptResponse.model_validate(self._decode_json(result.response))

    def delete(
        self, payload: DeleteReceiptRequest | dict[str, Any], *, headers: HeaderTypes | None = None
    ) -> DeleteReceiptResponse:
        payload = self._validate_payload(model=DeleteReceiptRequest, payload=payload)

        result = self._sync.send(
            "POST",
            self._path,
            headers=self._build_headers(self._headers, headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        self._ensure_http_success(result.response)

        return DeleteReceiptResponse.model_validate(self._decode_json(result.response))

    async def adelete(
        self, payload: DeleteReceiptRequest | dict[str, Any], *, headers: HeaderTypes | None = None
    ) -> DeleteReceiptResponse:
        payload = self._validate_payload(model=DeleteReceiptRequest, payload=payload)

        result = await self._async.send(
            "POST",
            self._path,
            headers=self._build_headers(self._headers, headers),
            payload=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

        self._ensure_http_success(result.response)

        return DeleteReceiptResponse.model_validate(self._decode_json(result.response))
