"""
HTTP transport layer. It concerns with:
* send request
* handle network errors
* handle non-2xx HTTP errors
* decode JSON (or 204/empty)
* produce structured context (request/response + metadata)
"""

from .async_transport import AsyncTransport
from .http import (
    HeaderTypes,
    HttpMethod,
    HttpRequestResponse,
    QueryParamTypes,
    parse_retry_after,
)
from .sync_transport import SyncTransport

__all__ = [
    "AsyncTransport",
    "SyncTransport",
    "HttpMethod",
    "HttpRequestResponse",
    "HeaderTypes",
    "QueryParamTypes",
    "parse_retry_after",
]
