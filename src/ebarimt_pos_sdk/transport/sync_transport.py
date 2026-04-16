import logging
import time
from typing import Any

import httpx

from ..errors import PosApiTransportError
from ..settings.retry_settings import RetrySettings
from .http import HttpMethod, HttpRequestResponse, QueryParamTypes, build_transport_error

logger = logging.getLogger(__name__)


class SyncTransport:
    def __init__(
        self,
        client: httpx.Client,
        retry: RetrySettings | None = None,
    ) -> None:
        self._client = client
        self._retry = retry or RetrySettings()

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
        last_request: httpx.Request | None = None
        response: httpx.Response | None = None
        for attempt in range(self._retry.max_retries):
            request = self._client.build_request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=payload,
                **kwargs,
            )
            last_request = request
            try:
                logger.debug("→ %s %s", method, url)
                response = self._client.send(request)
                logger.debug("← %s", response.status_code)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt < self._retry.max_retries - 1:
                    time.sleep(self._retry.sleep_seconds(attempt))
                    continue
                raise build_transport_error(request, exc) from exc
            except httpx.HTTPError as exc:
                raise build_transport_error(request, exc) from exc

            if response.status_code not in self._retry.retryable_statuses:
                return HttpRequestResponse(request=request, response=response)
            if attempt < self._retry.max_retries - 1:
                time.sleep(self._retry.sleep_seconds(attempt))

        if response is None or last_request is None:
            raise PosApiTransportError("retry loop exited without sending a request")
        return HttpRequestResponse(request=last_request, response=response)
