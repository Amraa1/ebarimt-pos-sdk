# src/ebarimt_pos_sdk/resources/receipt.py
from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from ..errors import PosApiDecodeError, PosApiHttpError, PosApiValidationError
from ..transport import AsyncTransport, HeaderTypes, SyncTransport

T = TypeVar("T", bound=BaseModel)

WHITE_LIST = {
    "terminal_id": "terminalID",
    "iban": "iBan",
    "operator_tin": "operatorTIN",
    "database_host": "database-host",
    "supported_databases": "supported-databases",
}


def alias_generator(s: str) -> str:
    if s in WHITE_LIST:
        return WHITE_LIST[s]

    parts = s.split("_")
    first = parts[0]
    rest: list[str] = []

    for word in parts[1:]:
        rest.append(word.title())

    return first + "".join(rest)


class BaseEbarimtModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        alias_generator=alias_generator,
        validate_by_name=True,  # allow snake_case input
        validate_by_alias=True,  # also allow camelCase input
    )


class BaseResource:
    def __init__(
        self,
        *,
        sync: SyncTransport,
        async_: AsyncTransport,
        headers: HeaderTypes | None = None,
    ) -> None:
        self._sync = sync
        self._async = async_
        self._headers = headers

    @property
    @abstractmethod
    def _path(self) -> str: ...

    @staticmethod
    def _decode_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except Exception as exc:
            raise PosApiDecodeError(
                "Failed to decode JSON response",
                response=response,
            ) from exc

    @staticmethod
    def _validate_payload(model: type[T], payload: T | dict[str, Any]) -> T:
        if isinstance(payload, model):
            return payload
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            raise PosApiValidationError(
                stage="request",
                model=model,
                validation_error=exc,
            ) from exc

    @staticmethod
    def _validate_response(model: type[T], response: Any) -> T:
        try:
            return model.model_validate(response)
        except ValidationError as exc:
            raise PosApiValidationError(
                stage="response",
                model=model,
                validation_error=exc,
            ) from exc

    @staticmethod
    def _build_headers(*headers: HeaderTypes | None) -> httpx.Headers:
        """Merges headers and returns one header.

        Note:
            Highest priority header should be the last.

        Returns:
            httpx.Headers: Merged header.
        """
        out = httpx.Headers()
        for header in headers:
            if header is not None:
                out.update(header)
        return out

    def _ensure_http_success(self, response: httpx.Response) -> httpx.Response:
        try:
            return response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            error = self._decode_json(response)
            raise PosApiHttpError(
                status=error["status"],
                message=str(error["message"]),
                date=datetime.fromisoformat(error["date"]),
                request=exc.request,
                response=exc.response,
                cause=exc,
            ) from exc
