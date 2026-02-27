from httpx import AsyncClient, Client

from .._types import HeaderTypes
from ..auth import PasswordGrantAuth
from ..resources import (
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
        *,
        sync_client: Client | None = None,
        async_client: AsyncClient | None = None,
        settings: ApiClientSettings,
        headers: HeaderTypes | None = None,
    ) -> None:
        """Ebarimt public api client."""

        super().__init__(
            sync_client=sync_client,
            async_client=async_client,
            settings=settings,
            headers=headers,
        )

        # OAuth2.0
        self.auth = PasswordGrantAuth(
            settings=settings,
            sync_client=self._sync_client,
            async_client=self._async_client,
            skew_seconds=settings.skew_seconds,
        )

        self._sync_client.auth = self.auth
        self._async_client.auth = self.auth

        # Resources
        self.district_code = DistrictCodeResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=headers,
        )

        self.tin_info = TinInfoResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=headers,
        )

        self.merchant_info = MerchantInfoResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=headers,
        )

        self.product_tax_code = ProductTaxCodeResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=headers,
        )
