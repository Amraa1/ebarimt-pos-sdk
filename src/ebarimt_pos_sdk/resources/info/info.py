from ..resource import BaseResource, HeaderTypes, _build_headers, _ensure_http_success
from .schema import ReadInfoResponse


class InfoResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/rest/info"

    def read(self, *, headers: HeaderTypes | None = None) -> ReadInfoResponse:
        result = self._sync.send(
            "GET",
            self._path,
            headers=_build_headers(self._headers, headers),
        )

        _ensure_http_success(result.response)

        return ReadInfoResponse.model_validate(result.response.json())

    async def aread(self, *, headers: HeaderTypes | None = None) -> ReadInfoResponse:
        result = await self._async.send(
            "GET",
            self._path,
            headers=_build_headers(self._headers, headers),
        )

        _ensure_http_success(result.response)

        return ReadInfoResponse.model_validate(result.response.json())
