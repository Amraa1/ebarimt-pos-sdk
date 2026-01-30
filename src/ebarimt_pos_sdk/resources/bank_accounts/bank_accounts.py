import httpx

from ..resource import BaseResource, HeaderTypes, _build_headers, _ensure_http_success
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
            headers=_build_headers(self._headers, headers),
        )

        success_response = _ensure_http_success(result.response)

        output: list[BankAccount] = []

        for data in success_response.json():
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
            headers=_build_headers(self._headers, headers),
        )

        success_response = _ensure_http_success(result.response)

        output: list[BankAccount] = []

        for data in success_response.json():
            output.append(BankAccount.model_validate(data))

        return output
