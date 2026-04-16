from __future__ import annotations

from typing import Any

from ...base_resource import BaseResource, HeaderTypes
from .schema import (
    CreateReceiptRequest,
    CreateReceiptResponse,
    DeleteReceiptRequest,
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
        return self._send_sync_request(
            "POST",
            payload_model=CreateReceiptRequest,
            payload=payload,
            response_model=CreateReceiptResponse,
            headers=headers,
        )

    async def acreate(
        self,
        payload: CreateReceiptRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateReceiptResponse:
        return await self._send_async_request(
            "POST",
            payload_model=CreateReceiptRequest,
            payload=payload,
            response_model=CreateReceiptResponse,
            headers=headers,
        )

    def delete(
        self, payload: DeleteReceiptRequest | dict[str, Any], *, headers: HeaderTypes | None = None
    ) -> None:
        self._send_sync_request(
            "DELETE",
            payload_model=DeleteReceiptRequest,
            payload=payload,
            headers=headers,
        )

    async def adelete(
        self, payload: DeleteReceiptRequest | dict[str, Any], *, headers: HeaderTypes | None = None
    ) -> None:
        await self._send_async_request(
            "DELETE",
            payload_model=DeleteReceiptRequest,
            payload=payload,
            headers=headers,
        )
