import logging

from .clients import EbarimtApiClient, EbarimtRestClient
from .errors import (
    PosApiBusinessError,
    PosApiDecodeError,
    PosApiError,
    PosApiHttpError,
    PosApiTransportError,
    PosApiValidationError,
)
from .factory import Environment, create_api_settings
from .resources import (
    BarCodeType,
    CreateReceiptRequest,
    CreateReceiptResponse,
    DeleteReceiptRequest,
    Item,
    Payment,
    PaymentCardData,
    PaymentCode,
    PaymentStatus,
    ReceiptCreateStatus,
    ReceiptItemData,
    ReceiptType,
    SubReceipt,
    TaxType,
)
from .settings import ApiClientSettings, RestClientSettings

# Library logging hygiene: attach a NullHandler so the SDK never emits to the
# root logger or prints "No handlers could be found" warnings. Applications opt
# in by configuring the "ebarimt_pos_sdk" logger themselves.
logging.getLogger("ebarimt_pos_sdk").addHandler(logging.NullHandler())

__all__ = [
    "EbarimtApiClient",
    "EbarimtRestClient",
    "RestClientSettings",
    "ApiClientSettings",
    "BarCodeType",
    "CreateReceiptRequest",
    "CreateReceiptResponse",
    "DeleteReceiptRequest",
    "Item",
    "create_api_settings",
    "Environment",
    "Payment",
    "PaymentCardData",
    "PaymentCode",
    "PaymentStatus",
    "SubReceipt",
    "ReceiptCreateStatus",
    "ReceiptItemData",
    "ReceiptType",
    "TaxType",
    "PosApiBusinessError",
    "PosApiDecodeError",
    "PosApiError",
    "PosApiHttpError",
    "PosApiTransportError",
    "PosApiValidationError",
]
