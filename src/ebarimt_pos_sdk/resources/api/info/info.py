from ...base_resource import BaseResource, HeaderTypes
from .schema import GetTinInfoResponse


class TinInfoResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/info/check/getTinInfo"

    def read(self, reg_no: str, *, headers: HeaderTypes | None = None) -> GetTinInfoResponse:
        return self._send_sync_request(
            "GET",
            params={"regNo": reg_no},
            headers=headers,
            response_model=GetTinInfoResponse,
        )

    async def aread(self, reg_no: str, *, headers: HeaderTypes | None = None) -> GetTinInfoResponse:
        return await self._send_async_request(
            "GET",
            params={"regNo": reg_no},
            headers=headers,
            response_model=GetTinInfoResponse,
        )
