from httpx import AsyncClient, Client

from .._types import HeaderTypes
from ..resources import (
    BunaResource,
    DistrictCodeResource,
    MerchantInfoResource,
    ProductTaxCodeResource,
    TinInfoResource,
)
from ..settings import ApiClientSettings
from .base_client import EbarimtBaseClient


class EbarimtApiClient(EbarimtBaseClient):
    def __init__(
        self,
        settings: ApiClientSettings,
        *,
        sync_client: Client | None = None,
        async_client: AsyncClient | None = None,
        headers: HeaderTypes | None = None,
    ) -> None:
        """Ebarimt public api client.

        These endpoints (district codes, TIN info, merchant info, product tax
        codes, BÜNA classification) are publicly readable — no OAuth2 token
        is required. The auth/ module is kept for future endpoints that may
        require it.
        """

        super().__init__(
            settings=settings,
            sync_client=sync_client,
            async_client=async_client,
            headers=headers,
        )

        # Resources
        self.district_code = DistrictCodeResource(
            sync=self._sync_transport,
            async_=self._async_transport,
        )

        self.tin_info = TinInfoResource(
            sync=self._sync_transport,
            async_=self._async_transport,
        )

        self.merchant_info = MerchantInfoResource(
            sync=self._sync_transport,
            async_=self._async_transport,
        )

        self.product_tax_code = ProductTaxCodeResource(
            sync=self._sync_transport,
            async_=self._async_transport,
        )

        self.buna = BunaResource(
            sync=self._sync_transport,
            async_=self._async_transport,
        )
