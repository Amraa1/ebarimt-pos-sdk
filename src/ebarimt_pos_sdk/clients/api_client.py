from httpx import AsyncClient, Client, Proxy

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
        proxy: str | Proxy | None = None,
    ) -> None:
        """Ebarimt public api client.

        These endpoints (district codes, TIN info, merchant info, product tax
        codes, BÜNA classification) are publicly readable — no OAuth2 token
        is required. The auth/ module is kept for future endpoints that may
        require it.

        ``proxy`` routes every request through an HTTP/SOCKS proxy — useful
        when the public API is only reachable from a specific region. Accepts a
        URL string (``"http://user:pass@host:8080"``) or an ``httpx.Proxy``;
        SOCKS proxies require the ``httpx[socks]`` extra. It cannot be combined
        with an injected ``sync_client``/``async_client`` — configure the proxy
        on that client instead.
        """

        super().__init__(
            settings=settings,
            sync_client=sync_client,
            async_client=async_client,
            headers=headers,
            proxy=proxy,
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
