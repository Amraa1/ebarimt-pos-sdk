from datetime import date

from pydantic import Field

from ...base_model import BaseEbarimtModel


class SaveMerchantRequest(BaseEbarimtModel):
    pos_no: str
    merchant_tins: list[str] = Field(min_length=1)


class SaveMerchantResponse(BaseEbarimtModel):
    msg: str
    status: int


class MerchantInfo(BaseEbarimtModel):
    name: str
    free_project: bool
    city_payer: bool
    vat_payer: bool
    found: bool
    vatpayer_registered_date: date
    is_government: bool


class GetInfoResponse(BaseEbarimtModel):
    msg: str
    status: int
    data: MerchantInfo
