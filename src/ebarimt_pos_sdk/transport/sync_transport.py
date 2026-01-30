from typing import Any

import httpx

from .http import HttpMethod, HttpRequestResponse, QueryParamTypes, build_transport_error


class SyncTransport:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def send(
        self,
        method: HttpMethod,
        url: httpx.URL | str,
        *,
        params: QueryParamTypes | None = None,
        headers: httpx.Headers | None = None,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> HttpRequestResponse:
        request = self._client.build_request(
            method=method,
            url=url,
            params=params,
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
