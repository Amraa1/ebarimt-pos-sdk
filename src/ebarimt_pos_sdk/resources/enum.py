from enum import Enum


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
    NO_VAT = "NO_VAT"


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
