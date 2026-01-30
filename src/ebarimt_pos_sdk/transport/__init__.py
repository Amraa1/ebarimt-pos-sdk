"""
This is the transport layer. It concerns with:
* send request
* handle network errors
* handle non-2xx HTTP errors
* decode JSON (or 204/empty)
* produce structured context (request/response + metadata)
"""

from .async_transport import AsyncTransport
from .http import HeaderTypes, HttpRequestResponse, QueryParamTypes
from .sync_transport import SyncTransport

__all__ = [
    "AsyncTransport",
    "SyncTransport",
    "HttpRequestResponse",
    "HeaderTypes",
    "QueryParamTypes",
]
