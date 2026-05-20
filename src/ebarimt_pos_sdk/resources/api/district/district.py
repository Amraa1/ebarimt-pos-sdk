from ...base_resource import BaseResource, HeaderTypes
from .schema import GetDistrictCodeResponse


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
