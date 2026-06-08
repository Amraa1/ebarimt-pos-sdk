import logging
import time
from typing import Any

import httpx

from .._logging import log_request, log_response, log_retry, new_request_id
from ..errors import PosApiTransportError
from ..settings.retry_settings import RetrySettings
from .http import (
    HeaderTypes,
    HttpMethod,
    HttpRequestResponse,
    QueryParamTypes,
    build_transport_error,
)

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
        headers: HeaderTypes | None = None,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> HttpRequestResponse:
        request_id = new_request_id()
        # Carried on the request so the error path (PosApiError) can read it
        # back and stay correlatable with the emitted log lines.
        extensions = {**kwargs.pop("extensions", {}), "request_id": request_id}
        last_request: httpx.Request | None = None
        response: httpx.Response | None = None
        for attempt in range(self._retry.max_retries):
            request = self._client.build_request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=payload,
                extensions=extensions,
                **kwargs,
            )
            last_request = request
            log_request(logger, request, request_id)
            started = time.perf_counter()
            try:
                response = self._client.send(request)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt < self._retry.max_retries - 1:
                    sleep_s = self._retry.sleep_seconds(attempt)
                    log_retry(
                        logger,
                        request_id,
                        attempt + 1,
                        self._retry.max_retries,
                        type(exc).__name__,
                        sleep_s,
                    )
                    time.sleep(sleep_s)
                    continue
                raise build_transport_error(request, exc) from exc
            except httpx.HTTPError as exc:
                raise build_transport_error(request, exc) from exc

            log_response(logger, response, request_id, (time.perf_counter() - started) * 1000)

            if response.status_code not in self._retry.retryable_statuses:
                return HttpRequestResponse(request=request, response=response)
            if attempt < self._retry.max_retries - 1:
                sleep_s = self._retry.sleep_seconds(attempt)
                log_retry(
                    logger,
                    request_id,
                    attempt + 1,
                    self._retry.max_retries,
                    str(response.status_code),
                    sleep_s,
                )
                time.sleep(sleep_s)

        if response is None or last_request is None:
            raise PosApiTransportError("retry loop exited without sending a request")
        return HttpRequestResponse(request=last_request, response=response)
