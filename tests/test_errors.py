from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest
from pydantic import BaseModel, ValidationError

# ✅ update import to your package path
from ebarimt_pos_sdk.errors import (
    PosApiBusinessError,
    PosApiDecodeError,
    PosApiError,
    PosApiHttpError,
    PosApiTransportError,
    PosApiValidationError,
)


def make_req_resp(status_code: int = 400) -> tuple[httpx.Request, httpx.Response]:
    req = httpx.Request("GET", "https://example.com/v1/resource")
    resp = httpx.Response(status_code=status_code, request=req, content=b'{"ok": false}')
    return req, resp


def test_pos_api_error_stores_fields_and_str() -> None:
    req, resp = make_req_resp(500)
    cause = RuntimeError("boom")

    err = PosApiError("something went wrong", request=req, response=resp, cause=cause)

    assert err.message == "something went wrong"
    assert err.request is req
    assert err.response is resp
    assert err.cause is cause

    s = str(err)
    assert "Message: something went wrong" in s
    assert "Request:" in s
    assert "Response:" in s
    assert "Cause: boom" in s  # RuntimeError("boom") string


def test_transport_decode_are_subclasses() -> None:
    err1 = PosApiTransportError("net")
    err2 = PosApiDecodeError("json")
    assert isinstance(err1, PosApiError)
    assert isinstance(err2, PosApiError)


def test_pos_api_http_error_message_format_includes_status_code_and_fields() -> None:
    req, resp = make_req_resp(403)
    dt = datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc)

    err = PosApiHttpError(
        status="FORBIDDEN",
        message="No permission",
        date=dt,
        request=req,
        response=resp,
        cause=None,
    )

    assert err.request is req
    assert err.response is resp
    assert err.status == "FORBIDDEN"
    assert err.date == dt

    s = str(err)
    assert "HTTP 403" in s
    assert "Status: FORBIDDEN" in s
    assert "Message: No permission" in s
    assert "Date: 2026-03-03" in s


def test_pos_api_business_error_fields() -> None:
    req, resp = make_req_resp(200)

    err = PosApiBusinessError(
        "domain failure",
        status="ERROR",
        code="E123",
        request=req,
        response=resp,
    )

    assert err.message == "domain failure"
    assert err.status == "ERROR"
    assert err.code == "E123"
    assert err.request is req
    assert err.response is resp


def test_pos_api_validation_error_request_stage_and_errors_property_and_str() -> None:
    class User(BaseModel):
        tin: str  # expecting str

    # Trigger a real ValidationError (tin is int)
    with pytest.raises(ValidationError) as ei:
        User.model_validate({"tin": 16000859970})

    ve = ei.value
    req, resp = make_req_resp(200)

    err = PosApiValidationError(
        stage="response",
        model=User,
        validation_error=ve,
        request=req,
        response=resp,
    )

    assert err.stage == "response"
    assert err.model == "User"
    assert err.validation_error is ve
    assert err.cause is ve  # inherited from PosApiError
    assert err.errors == ve.errors()

    s = str(err)
    assert "Validation failed during response for model 'User'" in s
    # The exact wording of pydantic messages can vary by version, so check structure:
    assert "tin" in s  # location printed
    assert "(" in s and ")" in s  # includes type in parentheses


def test_pos_api_validation_error_model_as_string() -> None:
    class M(BaseModel):
        x: int

    with pytest.raises(ValidationError) as ei:
        M.model_validate({"x": "nope"})
    ve = ei.value

    err = PosApiValidationError(stage="request", model="CustomName", validation_error=ve)
    assert err.model == "CustomName"
    assert "Validation failed during request for model 'CustomName'" in str(err)