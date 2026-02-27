from ...base_resource import BaseResource
from .schema import GetProductTaxCodeResponse


class ProductTaxCodeResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/receipt/receipt/getProductTaxCode"

    def read(self) -> GetProductTaxCodeResponse:
        return self._send_sync_request("GET", response_model=GetProductTaxCodeResponse)

    async def aread(self) -> GetProductTaxCodeResponse:
        return await self._send_async_request("GET", response_model=GetProductTaxCodeResponse)
