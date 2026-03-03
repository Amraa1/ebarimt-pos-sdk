from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, TypeVar, overload

import httpx
from pydantic import BaseModel, ValidationError

from ..errors import PosApiDecodeError, PosApiHttpError, PosApiValidationError
from ..transport import AsyncTransport, HeaderTypes, HttpMethod, QueryParamTypes, SyncTransport

T = TypeVar("T", bound=BaseModel)
N = TypeVar("N", bound=BaseModel)


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
        if response.status_code == 204:
            return None
        if not response.content:
            return None
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

    @staticmethod
    def _model_dump(payload: BaseModel) -> dict[str, Any]:
        return payload.model_dump(mode="json", by_alias=True, exclude_none=True)

    def _ensure_http_success(self, response: httpx.Response) -> httpx.Response:
        try:
            return response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            error: dict[str, Any] | None = self._decode_json(response)
            status = None
            date = None
            message = f"Http Error {response.status_code}, {exc.request}, {exc.response}."
            if error is not None:
                status = error.get("status")
                if error.get("date"):
                    date = datetime.fromisoformat(error["date"])
                if error.get("message"):
                    message = str(error["message"])

            raise PosApiHttpError(
                status=status,
                message=message,
                date=date,
                request=exc.request,
                response=exc.response,
                cause=exc,
            ) from exc

    @overload
    def _send_sync_request(
        self,
        method: HttpMethod,
        *,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: T | dict[str, Any] | None = None,
        response_model: None = None,
        headers: HeaderTypes | None = None,
    ) -> None: ...

    @overload
    def _send_sync_request(
        self,
        method: HttpMethod,
        *,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: T | dict[str, Any] | None = None,
        response_model: type[N],
        headers: HeaderTypes | None = None,
    ) -> N: ...

    def _send_sync_request(
        self,
        method: HttpMethod,
        *,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: T | dict[str, Any] | None = None,
        response_model: type[N] | None = None,
        headers: HeaderTypes | None = None,
    ) -> N | None:
        """Send sync request."""
        payload = None
        if payload_model and payload:
            payload = self._validate_payload(model=payload_model, payload=payload)
        elif not (payload_model or payload):
            pass
        else:
            raise ValueError("Both request model and payload must have a valid value.")

        if payload:
            result = self._sync.send(
                method,
                self._path,
                params=params,
                headers=self._build_headers(
                    self._headers,
                    headers,
                ),
                payload=self._model_dump(payload),
            )
        else:
            result = self._sync.send(
                method,
                self._path,
                params=params,
                headers=self._build_headers(
                    self._headers,
                    headers,
                ),
            )

        self._ensure_http_success(result.response)

        if response_model:
            return response_model.model_validate(self._decode_json(result.response))
        return None

    @overload
    async def _send_async_request(
        self,
        method: HttpMethod,
        *,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: T | dict[str, Any] | None = None,
        response_model: None = None,
        headers: HeaderTypes | None = None,
    ) -> None: ...

    @overload
    async def _send_async_request(
        self,
        method: HttpMethod,
        *,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: T | dict[str, Any] | None = None,
        response_model: type[N],
        headers: HeaderTypes | None = None,
    ) -> N: ...

    async def _send_async_request(
        self,
        method: HttpMethod,
        *,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: T | dict[str, Any] | None = None,
        response_model: type[N] | None = None,
        headers: HeaderTypes | None = None,
    ) -> N | None:
        """Send async request."""
        payload = None
        if payload_model and payload:
            payload = self._validate_payload(model=payload_model, payload=payload)
        elif not (payload_model or payload):
            pass
        else:
            raise ValueError("Both request model and payload must have a valid value.")

        if payload:
            result = await self._async.send(
                method,
                self._path,
                params=params,
                headers=self._build_headers(
                    self._headers,
                    headers,
                ),
                payload=self._model_dump(payload),
            )
        else:
            result = await self._async.send(
                method,
                self._path,
                params=params,
                headers=self._build_headers(
                    self._headers,
                    headers,
                ),
            )

        self._ensure_http_success(result.response)

        if response_model:
            return response_model.model_validate(self._decode_json(result.response))
        return None
