from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError

from ....errors import PosApiValidationError
from ...base_resource import BaseResource, HeaderTypes
from .schema import BankAccount


def _not_a_list_error(data: Any) -> ValidationError:
    """Build the pydantic error for a body that should have been a JSON array."""
    try:
        TypeAdapter(list[dict[str, Any]]).validate_python(data)
    except ValidationError as exc:
        return exc
    raise AssertionError("unreachable: data validated as a list")  # pragma: no cover


class BankAccountsResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/rest/bankAccounts"

    def _parse(self, response: httpx.Response) -> list[BankAccount]:
        self._ensure_http_success(response)
        data = self._decode_json(response)
        self._ensure_business_success(data, response)
        if not isinstance(data, list):
            raise PosApiValidationError(
                stage="response",
                model="list[BankAccount]",
                validation_error=_not_a_list_error(data),
                request=response.request,
                response=response,
            )
        return [self._validate_response(BankAccount, item, response=response) for item in data]

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
            headers=headers,
        )

        return self._parse(result.response)

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
            headers=headers,
        )

        return self._parse(result.response)
