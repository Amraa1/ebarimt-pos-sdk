import httpx

from ...base_resource import BaseResource, HeaderTypes
from .schema import BankAccount


class BankAccountsResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/rest/bankAccounts"

    def read(
        self,
        tin: str,
        *,
        headers: HeaderTypes | None = None,
    ) -> list[BankAccount]:
        result = self._sync.send(
            "GET",
            self._path,
            params=httpx.QueryParams({"tin": tin}),
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return [BankAccount.model_validate(data) for data in self._decode_json(result.response)]

    async def aread(
        self,
        tin: str,
        *,
        headers: HeaderTypes | None = None,
    ) -> list[BankAccount]:
        result = await self._async.send(
            "GET",
            self._path,
            params=httpx.QueryParams({"tin": tin}),
            headers=self._build_headers(self._headers, headers),
        )

        self._ensure_http_success(result.response)

        return [BankAccount.model_validate(data) for data in self._decode_json(result.response)]
