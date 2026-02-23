from pydantic import Field

from ...resource import BaseEbarimtModel


class SaveMerchantRequest(BaseEbarimtModel):
    pos_no: str
    merchant_tins: list[str] = Field(min_length=1)


class SaveMerchantResponse(BaseEbarimtModel):
    msg: str
    status: int
