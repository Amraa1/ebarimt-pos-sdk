from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, TypeAlias

import httpx

from ..errors import (
    PosApiTransportError,
)

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@dataclass(frozen=True)
class HttpRequestResponse:
    request: httpx.Request
    response: httpx.Response

    def as_tuple(self) -> tuple[httpx.Request, httpx.Response]:
        return (self.request, self.response)


def build_transport_error(
    request: httpx.Request,
    exc: httpx.HTTPError,
) -> PosApiTransportError:
    """Build Pos Api Transport layer error."""
    return PosApiTransportError(
        f"Transport error for {request.method} {request.url}: {exc}",
        request=request,
    )


PrimitiveData = str | int | float | bool | None

QueryParamTypes: TypeAlias = (
    httpx.QueryParams
    | Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
    | list[tuple[str, PrimitiveData]]
    | tuple[tuple[str, PrimitiveData], ...]
    | str
)
HeaderTypes: TypeAlias = (
    httpx.Headers
    | Mapping[str, str]
    | Mapping[bytes, bytes]
    | Sequence[tuple[str, str]]
    | Sequence[tuple[bytes, bytes]]
)
