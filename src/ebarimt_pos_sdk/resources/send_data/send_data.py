from ..resource import BaseResource, HeaderTypes


class SendDataResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/rest/sendData"

    def send(self, headers: HeaderTypes | None = None) -> None:
        result = self._sync.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return None

    async def asend(self, headers: HeaderTypes | None = None) -> None:
        result = await self._async.send(
            "GET",
            self._path,
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return None
