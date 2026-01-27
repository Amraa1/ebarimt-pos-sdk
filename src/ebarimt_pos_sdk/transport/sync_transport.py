from typing import Any

import httpx

from .http import HttpMethod, HttpRequestResponse, build_transport_error


class SyncTransport:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def send(
        self,
        method: HttpMethod,
        url: httpx.URL | str,
        *,
        headers: httpx.Headers | None = None,
        payload: dict[str, Any] | None = None,
        **kwargs,
    ) -> HttpRequestResponse:
        request = self._client.build_request(
            method=method,
            url=url,
            headers=headers,
            json=payload,
            **kwargs,
        )

        try:
            response = self._client.send(request)
        except httpx.HTTPError as exc:
            raise build_transport_error(request, exc) from exc

        return HttpRequestResponse(
            request=request,
            response=response,
        )
