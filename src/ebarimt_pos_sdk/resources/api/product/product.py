from ...base_resource import BaseResource, HeaderTypes
from .schema import GetProductTaxCodeResponse


class ProductTaxCodeResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/receipt/receipt/getProductTaxCode"

    def read(self, *, headers: HeaderTypes | None = None) -> GetProductTaxCodeResponse:
        return self._send_sync_request(
            "GET",
            headers=headers,
            response_model=GetProductTaxCodeResponse,
        )

    async def aread(self, *, headers: HeaderTypes | None = None) -> GetProductTaxCodeResponse:
        return await self._send_async_request(
            "GET",
            headers=headers,
            response_model=GetProductTaxCodeResponse,
        )
