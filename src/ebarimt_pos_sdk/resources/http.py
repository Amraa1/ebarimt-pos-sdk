# src/ebarimt_pos_sdk/resources/receipt.py
from __future__ import annotations

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from ..errors import PosApiHttpError

T = TypeVar("T", bound=BaseModel)


def raise_for_status(request: httpx.Request, response: httpx.Response):
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PosApiHttpError(
            f"Http status error: {response.status_code}", request=request, response=response
        ) from exc


def validate_payload(model: type[T], payload: T | dict[str, Any]) -> T:
    if isinstance(payload, model):
        return payload
    return model.model_validate(payload)
