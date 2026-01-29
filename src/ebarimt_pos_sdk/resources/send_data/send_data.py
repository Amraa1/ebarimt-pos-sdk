from ebarimt_pos_sdk.transport.async_transport import AsyncTransport
from ebarimt_pos_sdk.transport.sync_transport import SyncTransport

from ..resource import BaseResource, HeaderTypes, _build_headers, _ensure_http_success


class SendDataResource(BaseResource):
    def __init__(
        self,
        *,
        sync: SyncTransport,
        async_: AsyncTransport,
        headers: HeaderTypes | None = None,
    ) -> None:
        super().__init__(sync=sync, async_=async_, headers=headers)
        self._path = "/rest/sendData"

    def send(self, headers: HeaderTypes | None = None) -> None:
        result = self._sync.send(
            "GET",
            self._path,
            headers=_build_headers(self._headers, headers),
        )

        _ensure_http_success(result.response)

        return None

    async def asend(self, headers: HeaderTypes | None = None) -> None:
        result = await self._async.send(
            "GET",
            self._path,
            headers=_build_headers(self._headers, headers),
        )

        _ensure_http_success(result.response)

        return None
