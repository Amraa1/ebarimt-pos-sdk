from __future__ import annotations

from types import TracebackType

import httpx
from typing_extensions import Self

from .._types import HeaderTypes
from ..settings.base_settings import BaseSettings
from ..transport import AsyncTransport, SyncTransport


class EbarimtBaseClient:
    """
    Base client for Ebarimt SDK.
    """

    def __init__(
        self,
        settings: BaseSettings,
        *,
        sync_client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
        headers: HeaderTypes | None = None,
        proxy: str | httpx.Proxy | None = None,
    ) -> None:
        # A proxy can only be applied to a client the SDK builds itself. An
        # injected client is already constructed, so passing both is a
        # contradiction — configure the proxy on the injected client instead.
        if proxy is not None and (sync_client is not None or async_client is not None):
            raise ValueError(
                "proxy cannot be combined with an injected sync_client/async_client; "
                "configure the proxy on your injected client instead."
            )

        self._settings = settings
        self._headers = headers

        self._owns_sync = sync_client is None
        self._owns_async = async_client is None

        self._base_url = self._settings.base_url

        self._sync_client = sync_client or httpx.Client(
            base_url=self._base_url,
            timeout=settings.timeout_s,
            verify=settings.verify_tls,
            headers=headers,
            proxy=proxy,
        )
        self._async_client = async_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=settings.timeout_s,
            verify=settings.verify_tls,
            headers=headers,
            proxy=proxy,
        )

        # When the caller injects their own client, apply the SDK-level headers
        # to its defaults so client headers behave identically regardless of who
        # created the client. httpx merges these with per-request headers on
        # every outgoing request (per-request wins on key conflicts).
        if headers:
            if not self._owns_sync:
                self._sync_client.headers.update(headers)
            if not self._owns_async:
                self._async_client.headers.update(headers)

        self._sync_transport = SyncTransport(self._sync_client, retry=settings.retry)
        self._async_transport = AsyncTransport(self._async_client, retry=settings.retry)

    def close(self) -> None:
        if self._owns_sync:
            self._sync_client.close()

    async def aclose(self) -> None:
        if self._owns_async:
            await self._async_client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
