from ...base_resource import BaseResource, HeaderTypes
from .schema import ReadInfoResponse


class InfoResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/rest/info"

    def read(self, *, headers: HeaderTypes | None = None) -> ReadInfoResponse:
        return self._send_sync_request(
            "GET",
            response_model=ReadInfoResponse,
            headers=headers,
        )

    async def aread(self, *, headers: HeaderTypes | None = None) -> ReadInfoResponse:
        return await self._send_async_request(
            "GET",
            response_model=ReadInfoResponse,
            headers=headers,
        )
