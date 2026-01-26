from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .._http import _join_url, _merge_headers, _validate_model


class ReceiptCreateRequest(BaseModel):
    # Minimal subset to get real integrations working; we will expand from spec later.
    branchNo: str
    totalAmount: float
    merchantTin: str
    posNo: str
    type: str
    billIdSuffix: str
    receipts: list[dict[str, Any]]
    payments: Optional[list[dict[str, Any]]] = None

    # allow extra fields from real payloads
    model_config = {"extra": "allow"}


class ReceiptItemResponse(BaseModel):
    id: str
    bankAccountId: int

    model_config = {"extra": "allow"}


class ReceiptCreateResponse(BaseModel):
    id: str = Field(description="Багц төлбөрийн баримтын ДДТД (33 digits)")
    posId: int
    status: Literal["SUCCESS", "ERROR", "PAYMENT"]
    message: str
    qrDate: str
    lottery: str
    date: str
    easy: str
    receipts: list[ReceiptItemResponse]

    model_config = {"extra": "allow"}


class ReceiptResource:
    def __init__(
        self, *, base_url: str, headers: dict[str, str], transport: Any
    ) -> None:
        self._base_url = base_url
        self._headers = headers
        self._transport = transport

    def _url(self) -> str:
        return _join_url(self._base_url, "/rest/receipt")

    # Sync
    def create(
        self, payload: ReceiptCreateRequest | dict[str, Any]
    ) -> ReceiptCreateResponse:
        req = (
            payload
            if isinstance(payload, ReceiptCreateRequest)
            else _validate_model(ReceiptCreateRequest, payload, where="request")
        )
        data = self._transport.request_json(
            "POST",
            self._url(),
            headers=self._headers,
            json_body=req.model_dump(by_alias=True),
        )
        return _validate_model(ReceiptCreateResponse, data, where="response")

    # Async
    async def acreate(
        self, payload: ReceiptCreateRequest | dict[str, Any]
    ) -> ReceiptCreateResponse:
        req = (
            payload
            if isinstance(payload, ReceiptCreateRequest)
            else _validate_model(ReceiptCreateRequest, payload, where="request")
        )
        data = await self._transport.request_json(
            "POST",
            self._url(),
            headers=self._headers,
            json_body=req.model_dump(by_alias=True),
        )
        return _validate_model(ReceiptCreateResponse, data, where="response")
