from typing import Any

import httpx

from .http import (
    HeaderTypes,
    HttpMethod,
    HttpRequestResponse,
    QueryParamTypes,
    build_transport_error,
)


class AsyncTransport:
    """Async request/response transport layer."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def send(
        self,
        method: HttpMethod,
        url: httpx.URL | str,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> HttpRequestResponse:
        # build http request context
        request = self._client.build_request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            json=payload,
            **kwargs,
        )

        try:
            response = await self._client.send(request)
        except httpx.HTTPError as exc:
            raise build_transport_error(request, exc) from exc

        return HttpRequestResponse(
            request=request,
            response=response,
        )
