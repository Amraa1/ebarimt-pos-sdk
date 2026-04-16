from ...base_resource import BaseResource, HeaderTypes
from .schema import GetInfoResponse


class MerchantInfoResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/info/check/getInfo"

    def read(self, tin: str, *, headers: HeaderTypes | None = None) -> GetInfoResponse:
        return self._send_sync_request(
            "GET",
            params={"tin": tin},
            response_model=GetInfoResponse,
            headers=headers,
        )

    async def aread(self, tin: str, *, headers: HeaderTypes | None = None) -> GetInfoResponse:
        return await self._send_async_request(
            "GET",
            params={"tin": tin},
            response_model=GetInfoResponse,
            headers=headers,
        )
