from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal, TypeAlias

from pydantic import field_serializer

from ..resource import BaseEbarimtModel

# Json building block types
Number = Decimal | int | float


class ReceiptType(str, Enum):
    """Type of receipt or invoice issued to consumer or business."""

    B2C_RECEIPT = "B2C_RECEIPT"
    B2B_RECEIPT = "B2B_RECEIPT"
    B2C_INVOICE = "B2C_INVOICE"
    B2B_INVOICE = "B2B_INVOICE"


class TaxType(str, Enum):
    """VAT applicability of the receipt items."""

    VAT_ABLE = "VAT_ABLE"
    VAT_FREE = "VAT_FREE"
    VAT_ZERO = "VAT_ZERO"
    NOT_VAT = "NOT_VAT"


class BarCodeType(str, Enum):
    """Barcode standard used to identify the item."""

    UNDEFINED = "UNDEFINED"
    GS1 = "GS1"
    ISBN = "ISBN"


class PaymentCode(str, Enum):
    """Payment method used for the transaction."""

    CASH = "CASH"
    PAYMENT_CARD = "PAYMENT_CARD"


class PaymentStatus(str, Enum):
    """Current status of the payment."""

    PAID = "PAID"
    PAY = "PAY"
    REVERSED = "REVERSED"
    ERROR = "ERROR"


class ReceiptCreateStatus(str, Enum):
    """Result status returned after creating a receipt."""

    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PAYMENT = "PAYMENT"


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
    bar_code: str
    measure_unit: str
    qty: Number
    unit_price: Number
    total_amount: Number

    bar_code_type: _BarCodeType | None = None
    classification_code: str | None = None
    tax_product_code: str | None = None
    total_vat: Number | None = None
    total_city_tax: Number | None = None
    data: ReceiptItemData | None = None


class Receipt(BaseEbarimtModel):
    """Sub-receipt containing items, tax info, and seller details."""

    total_amount: Number
    tax_type: _TaxType
    merchant_tin: str
    items: list[Item]

    total_vat: Number | None = None
    total_city_tax: Number | None = None
    customer_tin: str | None = None

    bank_account_no: str | None = None
    iban: str | None = None
    invoice_id: str | None = None
    data: dict[str, Any] | None = None


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


class CreateReceiptBase(BaseEbarimtModel):
    """Base model for creating or returning a receipt."""

    branch_no: str
    total_amount: Number
    merchant_tin: str
    pos_no: str
    type: _ReceiptType
    receipts: list[Receipt]

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


class CreateReceiptRequest(CreateReceiptBase):
    """Request payload for creating a new receipt."""

    bill_id_suffix: str


class CreateReceiptResponse(CreateReceiptBase):
    """Response returned after receipt creation."""

    id: str
    version: str
    pos_id: int
    status: _ReceiptCreateStatus
    qr_data: str
    lottery: str
    date: datetime
    easy: bool


class DeleteReceiptRequest(BaseEbarimtModel):
    """Request payload for deleting an existing receipt."""

    id: str
    date: datetime
    type: _ReceiptType

    @field_serializer("date")
    def serialize_date(self, value: datetime) -> str:
        # Ebarimt expects: yyyy-mm-dd hh:mm:ss
        return value.strftime("%Y-%m-%d %H:%M:%S")


class DeleteReceiptResponse(BaseEbarimtModel):
    """Response returned after deleting a receipt."""

    pass

    # TODO
