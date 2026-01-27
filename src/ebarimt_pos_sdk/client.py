from __future__ import annotations

import httpx

from .resources.receipt.receipt import ReceiptResource
from .settings import PosApiSettings
from .transport import AsyncTransport, SyncTransport


class PosApiClient:
    """
    Dual sync/async client.

    Usage:
        client = PosApiClient(PosApiSettings(...))
        resp = client.receipt.create({...})

        async with PosApiClient(...) as client:
            resp = await client.receipt.acreate({...})
    """

    def __init__(
        self,
        settings: PosApiSettings,
        *,
        sync_client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
        headers: httpx.Headers | None = None,
    ) -> None:
        self._settings = settings
        self._headers = headers

        self._owns_sync = sync_client is None
        self._owns_async = async_client is None

        self._base_url = self._settings.base_url

        self._sync_client = sync_client or httpx.Client(
            base_url=self._base_url,
            timeout=settings.timeout_s,
            verify=settings.verify_tls,
        )
        self._async_client = async_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=settings.timeout_s,
            verify=settings.verify_tls,
        )

        self._sync_transport = SyncTransport(self._sync_client)
        self._async_transport = AsyncTransport(self._async_client)

        # Resources
        self.receipt = ReceiptResource(
            sync=self._sync_transport,
            async_=self._async_transport,
            headers=self._headers,
        )

    def close(self) -> None:
        if self._owns_sync:
            self._sync_client.close()

    async def aclose(self) -> None:
        if self._owns_async:
            await self._async_client.aclose()

    async def __aenter__(self) -> PosApiClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def __enter__(self) -> PosApiClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
