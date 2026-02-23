from ...resource import BaseResource, HeaderTypes
from .schema import GetDistrictCodeResponse, GetTinInfoResponse


class DistrictCodeResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/info/check/getBranchInfo"

    def read(self, *, headers: HeaderTypes | None = None) -> GetDistrictCodeResponse:
        result = self._sync.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return GetDistrictCodeResponse.model_validate(self._decode_json(result.response))

    async def aread(self, *, headers: HeaderTypes | None = None) -> GetTinInfoResponse:
        result = await self._async.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return GetTinInfoResponse.model_validate(self._decode_json(result.response))


class TinInfoResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/info/check/getTinInfo"

    def read(self, *, headers: HeaderTypes | None = None) -> GetTinInfoResponse:
        result = self._sync.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return GetTinInfoResponse.model_validate(self._decode_json(result.response))

    async def aread(self, *, headers: HeaderTypes | None = None) -> GetDistrictCodeResponse:
        result = await self._async.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return GetDistrictCodeResponse.model_validate(self._decode_json(result.response))
