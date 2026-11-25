from typing import Annotated

from pydantic import Field, StringConstraints

from ...base_model import BaseEbarimtModel

# 11-digit taxpayer identification number (structure only; whether eBarimt
# knows the TIN is the server's call).
Tin = Annotated[str, StringConstraints(pattern=r"^\d{11}$")]


class CreateMerchantRegistrationRequest(BaseEbarimtModel):
    """Request to register merchants under an operator's POS (``saveOprMerchants``)."""

    pos_no: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    merchant_tins: list[Tin] = Field(min_length=1)


class CreateMerchantRegistrationResponse(BaseEbarimtModel):
    """eBarimt's acknowledgement that the registration request was received.

    It does not mean the merchants are registered: approval is asynchronous.
    """

    msg: str
    status: int
