from httpx import AsyncClient, Client, Proxy

from .._types import HeaderTypes
from ..auth import PasswordGrantAuth
from ..resources import (
    BunaResource,
    DistrictCodeResource,
    MerchantInfoResource,
    MerchantRegistrationResource,
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

        The info endpoints (district codes, TIN info, merchant info, product
        tax codes, BÜNA classification) are publicly readable — no OAuth2
        token is required, and the client sends none to them even when the
        settings carry credentials.

        ``merchant_registration`` is the exception: it sends a password-grant
        token and ``X-API-KEY`` from the settings, on its own requests only.
        The token is fetched through this client's own HTTP clients, so it
        uses the same proxy, TLS and timeout settings.

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

        # Built only when the password-grant fields are all present; building
        # it makes no network call. Only merchant_registration receives it.
        token_auth = (
            PasswordGrantAuth(
                settings=settings,
                sync_client=self._sync_client,
                async_client=self._async_client,
                skew_seconds=settings.skew_seconds,
            )
            if settings.has_password_grant_credentials
            else None
        )
        self.merchant_registration = MerchantRegistrationResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            settings=settings,
            token_auth=token_auth,
        )
