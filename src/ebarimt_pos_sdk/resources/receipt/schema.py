from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

# Json building block types
Number = Decimal | int | float


class ReceiptType(str, Enum):
    B2C_RECEIPT = "B2C_RECEIPT"
    B2B_RECEIPT = "B2B_RECEIPT"
    B2C_INVOICE = "B2C_INVOICE"
    B2B_INVOICE = "B2B_INVOICE"


class TaxType(str, Enum):
    VAT_ABLE = "VAT_ABLE"
    VAT_FREE = "VAT_FREE"
    VAT_ZERO = "VAT_ZERO"
    NOT_VAT = "NOT_VAT"


class BarCodeType(str, Enum):
    UNDEFINED = "UNDEFINED"
    GS1 = "GS1"
    ISBN = "ISBN"


class PaymentCode(str, Enum):
    CASH = "CASH"
    PAYMENT_CARD = "PAYMENT_CARD"


class PaymentStatus(str, Enum):
    PAID = "PAID"
    PAY = "PAY"
    REVERSED = "REVERSED"
    ERROR = "ERROR"


class ReceiptCreateStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PAYMENT = "PAYMENT"


class ReceiptItemData(BaseModel):
    """
    items[].data
    Note: docs show lotNo + stockQR, but examples also show nested "data": {"stockQR":[...]} sometimes.
    This model follows the schema: lotNo, stockQR directly under data.
    """

    model_config = ConfigDict(extra="ignore")

    lotNo: str | None = None
    stockQR: list[str] | None = None


class Item(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    barCode: str
    measureUnit: str
    qty: Number
    unitPrice: Number
    totalAmount: Number

    barCodeType: BarCodeType | str | None = None
    classificationCode: str | None = None
    taxProductCode: str | None = None
    totalVAT: Number | None = None
    totalCityTax: Number | None = None
    data: ReceiptItemData | None = None


class Receipt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    totalAmount: Number
    taxType: TaxType | str
    merchantTin: str
    items: list[Item]

    totalVAT: Number | None = None
    totalCityTax: Number | None = None
    customerTin: str | None = None

    bankAccountNo: str | None = None
    iBan: str | None = None
    invoiceId: str | None = None
    data: dict[str, Any] | None = None


class PaymentCardData(BaseModel):
    """
    payments[].data when code=PAYMENT_CARD
    """

    model_config = ConfigDict(extra="ignore")

    terminalID: str
    rrn: str
    maskedCardNumber: str
    easy: bool
    bankCode: str | None = None


class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: PaymentCode | str
    status: PaymentStatus | str
    paidAmount: Number

    exchangeCode: str | None = None
    data: PaymentCardData | None = None  # Only when code is PAYMENT_CARD


class CreateReceiptRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    branchNo: str
    totalAmount: Number
    merchantTin: str
    posNo: str
    type: ReceiptType | str
    billIdSuffix: str
    receipts: list[Receipt]

    totalVAT: Number | None = None
    totalCityTax: Number | None = None
    districtCode: str | None = None
    customerTin: str | None = None
    consumerNo: str | None = None
    inactiveId: str | None = None
    invoiceId: str | None = None
    reportMonth: str | None = None
    data: dict[str, Any] | None = None

    payments: list[Payment] | None = None


class ReceiptItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    bankAccountId: int


class CreateReceiptResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    posId: int
    status: ReceiptCreateStatus | str
    message: str
    qrDate: str
    lottery: str
    date: datetime
    easy: bool
    receipts: list[ReceiptItemResponse]
