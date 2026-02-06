import httpx

from ..resource import BaseResource, HeaderTypes
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

        response = self._ensure_http_success(result.response)

        output: list[BankAccount] = []

        for data in self._decode_json(response):
            output.append(BankAccount.model_validate(data))

        return output

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

        response = self._ensure_http_success(result.response)

        output: list[BankAccount] = []

        for data in self._decode_json(response):
            output.append(BankAccount.model_validate(data))

        return output
