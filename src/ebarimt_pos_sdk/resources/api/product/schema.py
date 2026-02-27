from datetime import datetime

from ...base_model import BaseEbarimtModel
from ...enum import TaxType


class ProductTaxCode(BaseEbarimtModel):
    start_date: datetime
    end_date: datetime | None = None
    tax_product_code: str
    tax_product_name: str
    tax_type_code: int
    tax_type_name: TaxType


class GetProductTaxCodeResponse(BaseEbarimtModel):
    msg: str
    status: int
    data: list[ProductTaxCode]
