from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal, TypeAlias

from pydantic import field_serializer, field_validator

from ...base_model import BaseEbarimtModel
from ...enum import (
    BarCodeType,
    PaymentCode,
    PaymentStatus,
    ReceiptCreateStatus,
    ReceiptType,
    TaxType,
)

# Json building block types
Number = Decimal | int | float


_ReceiptType: TypeAlias = (
    ReceiptType | Literal["B2C_RECEIPT", "B2B_RECEIPT", "B2C_INVOICE", "B2B_INVOICE"]
)

_TaxType = TaxType | Literal["VAT_ABLE", "VAT_FREE", "VAT_ZERO", "NOT_VAT"]

_BarCodeType: TypeAlias = BarCodeType | Literal["UNDEFINED", "GS1", "ISBN"]

_PaymentCode: TypeAlias = PaymentCode | Literal["CASH", "PAYMENT_CARD"]

_PaymentStatus: TypeAlias = PaymentStatus | Literal["PAID", "PAY", "REVERSED", "ERROR"]

_ReceiptCreateStatus = ReceiptCreateStatus | Literal["SUCCESS", "ERROR", "PAYMENT"]


class ReceiptItemData(BaseEbarimtModel):
    """
    items[].data
    Note: docs show lotNo + stockQR, but examples also show nested "data": {"stockQR":[...]} sometimes.
    This model follows the schema: lotNo, stockQR directly under data.
    """

    lotNo: str | None = None
    stockQR: list[str] | None = None


class Item(BaseEbarimtModel):
    """Single product or service included in a receipt."""

    name: str
    measure_unit: str
    qty: Number
    unit_price: Number
    total_amount: Number

    @field_validator("qty", "unit_price")
    @classmethod
    def validate_positive(cls, v: Number) -> Number:
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v

    bar_code: str | None = None
    bar_code_type: _BarCodeType | None = None
    classification_code: str | None = None
    tax_product_code: str | None = None
    total_vat: Number | None = None
    total_city_tax: Number | None = None
    data: ReceiptItemData | None = None


class SubReceipt(BaseEbarimtModel):
    """Sub-receipt containing items, tax info, and seller details."""

    total_amount: Number
    tax_type: _TaxType
    merchant_tin: str
    items: list[Item]

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v: list[Item]) -> list[Item]:
        if not v:
            raise ValueError("items must not be empty")
        return v

    total_vat: Number | None = None
    total_city_tax: Number | None = None
    customer_tin: str | None = None

    bank_account_no: str | None = None
    iban: str | None = None
    invoice_id: str | None = None
    data: dict[str, Any] | None = None


class SubReceiptResponse(SubReceipt):
    id: str


class PaymentCardData(BaseEbarimtModel):
    """Card payment metadata when using PAYMENT_CARD."""

    terminal_id: str
    rrn: str
    masked_card_number: str
    easy: bool
    bank_code: str | None = None


class Payment(BaseEbarimtModel):
    """Payment information associated with a receipt."""

    code: _PaymentCode
    status: _PaymentStatus
    paid_amount: Number

    exchange_code: str | None = None
    data: PaymentCardData | None = None  # Only when code is PAYMENT_CARD


class _CreateReceiptBase(BaseEbarimtModel):
    """Base model for creating or returning a receipt."""

    branch_no: str
    total_amount: Number
    merchant_tin: str
    pos_no: str
    type: _ReceiptType

    # Need to define receipts: list[ReceiptBase]

    total_vat: Number | None = None
    total_city_tax: Number | None = None
    district_code: str | None = None
    customer_tin: str | None = None
    consumer_no: str | None = None
    inactive_id: str | None = None
    invoice_id: str | None = None
    report_month: str | None = None
    data: dict[str, Any] | None = None

    payments: list[Payment] | None = None


class CreateReceiptRequest(_CreateReceiptBase):
    """Request payload for creating a new receipt."""

    bill_id_suffix: str
    receipts: list[SubReceipt]


class CreateReceiptResponse(_CreateReceiptBase):
    """Response returned after receipt creation."""

    id: str
    version: str
    pos_id: int
    status: _ReceiptCreateStatus
    qr_data: str
    lottery: str
    date: datetime
    easy: bool
    receipts: list[SubReceiptResponse]

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: str | datetime) -> datetime:
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return datetime.strptime(v, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


class DeleteReceiptRequest(BaseEbarimtModel):
    """Request payload for deleting an existing receipt."""

    id: str
    date: datetime | None = None

    @field_serializer("date")
    def serialize_date(self, value: datetime | None) -> str | None:
        # Ebarimt expects: yyyy-mm-dd hh:mm:ss
        if value is None:
            return value
        return value.strftime("%Y-%m-%d %H:%M:%S")
