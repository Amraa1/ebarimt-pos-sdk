from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, TypeVar, overload

import httpx
from pydantic import BaseModel, ValidationError

from .._redaction import redact_url
from ..errors import (
    PosApiBusinessError,
    PosApiDecodeError,
    PosApiHttpError,
    PosApiValidationError,
)
from ..transport import AsyncTransport, HeaderTypes, HttpMethod, QueryParamTypes, SyncTransport

T = TypeVar("T", bound=BaseModel)
N = TypeVar("N", bound=BaseModel)


class BaseResource:
    # Values of a 2xx body's ``status`` field that denote a domain-level
    # failure (PosAPI 3.0: "ERROR — Төлбөрийн баримтын мэдээлэл үүсгэхэд алдаа
    # гарсан"). Structural check only: the SDK does not interpret *why* the
    # server rejected the request. Subclasses may override.
    _business_error_statuses: frozenset[str] = frozenset({"ERROR"})

    def __init__(
        self,
        *,
        sync: SyncTransport,
        async_: AsyncTransport,
    ) -> None:
        self._sync = sync
        self._async = async_

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
        except ValueError as exc:
            raise PosApiDecodeError(
                "Failed to decode JSON response",
                response=response,
            ) from exc

    @staticmethod
    def _validate_payload(model: type[T], payload: BaseModel | dict[str, Any]) -> T:
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
    def _validate_response(
        model: type[T],
        data: Any,
        *,
        response: httpx.Response | None = None,
    ) -> T:
        """Validate a decoded 2xx body against ``model``, surfacing failures as
        ``PosApiValidationError(stage="response")`` rather than a bare pydantic
        ``ValidationError``."""
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise PosApiValidationError(
                stage="response",
                model=model,
                validation_error=exc,
                request=response.request if response is not None else None,
                response=response,
            ) from exc

    def _ensure_business_success(self, data: Any, response: httpx.Response) -> None:
        """Raise ``PosApiBusinessError`` when a 2xx body carries an error status.

        PosAPI reports some failures (e.g. receipt rejected) with HTTP 200 and
        ``{"status": "ERROR", "message": "..."}``. Such a body usually lacks the
        fields of the success model, so without this check it would surface as
        a misleading response-validation error.
        """
        if not isinstance(data, dict):
            return
        status = data.get("status")
        if not isinstance(status, str) or status not in self._business_error_statuses:
            return
        message = data.get("message")
        raise PosApiBusinessError(
            str(message) if message else f"Server returned status {status!r}",
            status=status,
            code=data.get("code"),
            request=response.request,
            response=response,
        )

    @staticmethod
    def _model_dump(payload: BaseModel) -> dict[str, Any]:
        return payload.model_dump(mode="json", by_alias=True, exclude_none=True)

    def _prepare_send_kwargs(
        self,
        *,
        params: QueryParamTypes | None,
        payload_model: type[T] | None,
        payload: BaseModel | dict[str, Any] | None,
        headers: HeaderTypes | None,
    ) -> dict[str, Any]:
        """Validate payload, merge headers, build the kwargs dict for transport.send()."""
        if payload_model is not None and payload is not None:
            validated = self._validate_payload(model=payload_model, payload=payload)
        elif payload_model is None and payload is None:
            validated = None
        else:
            raise ValueError("Both request model and payload must have a valid value.")

        kwargs: dict[str, Any] = {
            "params": params,
            "headers": headers,
        }
        if validated is not None:
            kwargs["payload"] = self._model_dump(validated)
        return kwargs

    def _decode_and_validate(
        self,
        response: httpx.Response,
        response_model: type[N] | None,
    ) -> N | None:
        self._ensure_http_success(response)
        if response_model is None:
            # No body expected (e.g. receipt delete). Still inspect a JSON body
            # for a business error, but tolerate non-JSON/empty bodies.
            try:
                data = self._decode_json(response)
            except PosApiDecodeError:
                return None
            self._ensure_business_success(data, response)
            return None
        data = self._decode_json(response)
        self._ensure_business_success(data, response)
        return self._validate_response(response_model, data, response=response)

    def _ensure_http_success(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            error: Any = None
            try:
                error = self._decode_json(response)
            except PosApiDecodeError:
                # Some upstream error pages return HTML/plain text instead of JSON.
                # Preserve the HTTP error and fall back to the generic message.
                error = None
            status = None
            date = None
            # Fallback message uses the *redacted* URL — httpx's Request repr
            # would embed raw query params (e.g. tokens) verbatim.
            message = (
                f"Http Error {response.status_code} for "
                f"{exc.request.method} {redact_url(exc.request.url)}."
            )
            if isinstance(error, dict):
                status = error.get("status")
                if error.get("date"):
                    # Never let a malformed date raise *inside* the error
                    # handler and mask the real HTTP error.
                    try:
                        date = datetime.fromisoformat(str(error["date"]))
                    except ValueError:
                        date = None
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
        path: str | None = None,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: BaseModel | dict[str, Any] | None = None,
        response_model: None = None,
        headers: HeaderTypes | None = None,
    ) -> None: ...

    @overload
    def _send_sync_request(
        self,
        method: HttpMethod,
        *,
        path: str | None = None,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: BaseModel | dict[str, Any] | None = None,
        response_model: type[N],
        headers: HeaderTypes | None = None,
    ) -> N: ...

    def _send_sync_request(
        self,
        method: HttpMethod,
        *,
        path: str | None = None,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: BaseModel | dict[str, Any] | None = None,
        response_model: type[N] | None = None,
        headers: HeaderTypes | None = None,
    ) -> N | None:
        """Send sync request. `path` overrides `self._path` for resources
        that build the URL dynamically (e.g. hierarchical drill-down)."""
        send_kwargs = self._prepare_send_kwargs(
            params=params,
            payload_model=payload_model,
            payload=payload,
            headers=headers,
        )
        result = self._sync.send(method, path or self._path, **send_kwargs)
        return self._decode_and_validate(result.response, response_model)

    @overload
    async def _send_async_request(
        self,
        method: HttpMethod,
        *,
        path: str | None = None,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: BaseModel | dict[str, Any] | None = None,
        response_model: None = None,
        headers: HeaderTypes | None = None,
    ) -> None: ...

    @overload
    async def _send_async_request(
        self,
        method: HttpMethod,
        *,
        path: str | None = None,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: BaseModel | dict[str, Any] | None = None,
        response_model: type[N],
        headers: HeaderTypes | None = None,
    ) -> N: ...

    async def _send_async_request(
        self,
        method: HttpMethod,
        *,
        path: str | None = None,
        params: QueryParamTypes | None = None,
        payload_model: type[T] | None = None,
        payload: BaseModel | dict[str, Any] | None = None,
        response_model: type[N] | None = None,
        headers: HeaderTypes | None = None,
    ) -> N | None:
        """Send async request. `path` overrides `self._path` for resources
        that build the URL dynamically (e.g. hierarchical drill-down)."""
        send_kwargs = self._prepare_send_kwargs(
            params=params,
            payload_model=payload_model,
            payload=payload,
            headers=headers,
        )
        result = await self._async.send(method, path or self._path, **send_kwargs)
        return self._decode_and_validate(result.response, response_model)
