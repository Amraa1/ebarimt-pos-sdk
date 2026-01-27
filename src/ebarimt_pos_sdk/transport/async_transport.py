from typing import Any

import httpx

from .http import (
    HttpMethod,
    HttpRequestResponse,
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
        headers: httpx.Headers | None = None,
        payload: dict[str, Any] | None = None,
        **kwargs,
    ) -> HttpRequestResponse:
        # build http request context
        request = self._client.build_request(
            method=method,
            url=url,
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
