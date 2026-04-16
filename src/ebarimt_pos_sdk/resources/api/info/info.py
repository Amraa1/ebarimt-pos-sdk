from ...base_resource import BaseResource, HeaderTypes
from .schema import GetDistrictCodeResponse, GetTinInfoResponse


class DistrictCodeResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/info/check/getBranchInfo"

    def read(self, *, headers: HeaderTypes | None = None) -> GetDistrictCodeResponse:
        return self._send_sync_request(
            "GET",
            headers=headers,
            response_model=GetDistrictCodeResponse,
        )

    async def aread(self, *, headers: HeaderTypes | None = None) -> GetDistrictCodeResponse:
        return await self._send_async_request(
            "GET",
            headers=headers,
            response_model=GetDistrictCodeResponse,
        )


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
