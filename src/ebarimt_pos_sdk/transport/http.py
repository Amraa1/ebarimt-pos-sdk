from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx

from ..errors import (
    PosApiTransportError,
)

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@dataclass(frozen=True)
class HttpRequestResponse:
    request: httpx.Request
    response: httpx.Response

    def as_tuple(self):
        return self.request, self.response


def build_transport_error(
    request: httpx.Request,
    exc: httpx.HTTPError,
):
    """Build Pos Api Transport layer error."""
    return PosApiTransportError(
        f"Transport error for {request.method} {request.url}: {exc}",
        request=request,
    )
