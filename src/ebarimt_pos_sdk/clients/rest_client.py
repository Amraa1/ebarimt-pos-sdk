from __future__ import annotations

import httpx

from .._types import HeaderTypes
from ..resources import BankAccountsResource, InfoResource, ReceiptResource, SendDataResource
from ..settings.rest_client_settings import RestClientSettings
from .base_client import EbarimtBaseClient


class EbarimtRestClient(EbarimtBaseClient):
    """Ebarimt REST api client."""

    def __init__(
        self,
        settings: RestClientSettings,
        *,
        sync_client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
        headers: HeaderTypes | None = None,
    ) -> None:
        super().__init__(
            settings=settings,
            sync_client=sync_client,
            async_client=async_client,
            headers=headers,
        )

        # Resources
        self.receipt = ReceiptResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=self._headers,
        )
        self.info = InfoResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=self._headers,
        )
        self.send_data = SendDataResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=self._headers,
        )
        self.bank_accounts = BankAccountsResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=self._headers,
        )
