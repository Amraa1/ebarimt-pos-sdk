from ..resource import BaseResource, HeaderTypes
from .schema import ReadInfoResponse


class InfoResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/rest/info"

    def read(self, *, headers: HeaderTypes | None = None) -> ReadInfoResponse:
        result = self._sync.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return ReadInfoResponse.model_validate(self._decode_json(result.response))

    async def aread(self, *, headers: HeaderTypes | None = None) -> ReadInfoResponse:
        result = await self._async.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return ReadInfoResponse.model_validate(self._decode_json(result.response))
