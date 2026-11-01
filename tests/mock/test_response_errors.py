"""Regression tests for issues #78, #79 and #82 (item 1):

* a 2xx body with ``status: "ERROR"`` raises ``PosApiBusinessError``;
* a malformed 2xx body raises ``PosApiValidationError(stage="response")``,
  never a bare ``pydantic.ValidationError``;
* a malformed ``date`` in a non-2xx error body does not mask the HTTP error.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from pydantic import ValidationError

from ebarimt_pos_sdk import (
    EbarimtRestClient,
    PosApiBusinessError,
    PosApiHttpError,
    PosApiValidationError,
    RestClientSettings,
)

from ..helpers import BASE_REST_URL

SUCCESS_REQUEST = {
    "branchNo": "001",
    "totalAmount": 1000,
    "merchantTin": "12345678901",
    "posNo": "001",
    "type": "B2C_RECEIPT",
    "billIdSuffix": "01",
    "receipts": [
        {
            "totalAmount": 1000,
            "taxType": "VAT_ABLE",
            "merchantTin": "12345678901",
            "items": [
                {
                    "name": "Bread",
                    "barCode": "19059010880001",
                    "measureUnit": "senlovesfits",
                    "qty": 1,
                    "unitPrice": 1000,
                    "totalAmount": 1000,
                }
            ],
        }
    ],
}

BUSINESS_ERROR_BODY = {
    "status": "ERROR",
    "message": "Татварын дугаар буруу байна",
    "date": "2026-11-01 10:00:00",
}


def _client() -> EbarimtRestClient:
    return EbarimtRestClient(RestClientSettings(base_url=BASE_REST_URL))


# --- #78: PosApiBusinessError --------------------------------------------------


@respx.mock
def test_receipt_create_sync_business_error() -> None:
    route = respx.post(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(200, json=BUSINESS_ERROR_BODY)
    )
    with _client() as client, pytest.raises(PosApiBusinessError) as exc_info:
        client.receipt.create(SUCCESS_REQUEST)
    err = exc_info.value
    assert route.called
    assert err.status == "ERROR"
    assert err.message == BUSINESS_ERROR_BODY["message"]
    assert err.response is not None and err.response.status_code == 200
    assert err.request_id is not None


@pytest.mark.asyncio
@respx.mock
async def test_receipt_create_async_business_error() -> None:
    respx.post(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(200, json=BUSINESS_ERROR_BODY)
    )
    async with _client() as client:
        with pytest.raises(PosApiBusinessError) as exc_info:
            await client.receipt.acreate(SUCCESS_REQUEST)
    assert exc_info.value.status == "ERROR"


@respx.mock
def test_business_error_without_message_has_fallback_text() -> None:
    respx.post(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(200, json={"status": "ERROR"})
    )
    with _client() as client, pytest.raises(PosApiBusinessError, match="status 'ERROR'"):
        client.receipt.create(SUCCESS_REQUEST)


@respx.mock
def test_non_error_status_is_not_a_business_error() -> None:
    # "PAYMENT" is a legitimate receipt state, not a rejection — it must flow
    # through to model validation (which fails here only because the body is
    # deliberately minimal).
    respx.post(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(200, json={"status": "PAYMENT"})
    )
    with _client() as client, pytest.raises(PosApiValidationError):
        client.receipt.create(SUCCESS_REQUEST)


# --- #79: response validation is wrapped -------------------------------------


@respx.mock
def test_receipt_create_malformed_body_raises_sdk_validation_error() -> None:
    respx.post(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(200, json={"id": "x", "status": "SUCCESS"})
    )
    with _client() as client, pytest.raises(PosApiValidationError) as exc_info:
        client.receipt.create(SUCCESS_REQUEST)
    err = exc_info.value
    assert err.stage == "response"
    assert err.model == "CreateReceiptResponse"
    assert err.response is not None and err.response.status_code == 200
    assert isinstance(err.cause, ValidationError)
    assert any("qrData" in ".".join(map(str, e["loc"])) for e in err.errors)


@respx.mock
def test_info_read_malformed_body_raises_sdk_validation_error() -> None:
    respx.get(f"{BASE_REST_URL}/rest/info").mock(
        return_value=httpx.Response(200, json={"unexpected": True})
    )
    with _client() as client, pytest.raises(PosApiValidationError) as exc_info:
        client.info.read()
    assert exc_info.value.stage == "response"
    assert exc_info.value.model == "ReadInfoResponse"


@pytest.mark.asyncio
@respx.mock
async def test_info_aread_malformed_body_raises_sdk_validation_error() -> None:
    respx.get(f"{BASE_REST_URL}/rest/info").mock(
        return_value=httpx.Response(200, json={"unexpected": True})
    )
    async with _client() as client:
        with pytest.raises(PosApiValidationError) as exc_info:
            await client.info.aread()
    assert exc_info.value.stage == "response"


@respx.mock
def test_bank_accounts_malformed_item_raises_sdk_validation_error() -> None:
    respx.get(f"{BASE_REST_URL}/rest/bankAccounts").mock(
        return_value=httpx.Response(200, json=[{"bogus": 1}])
    )
    with _client() as client, pytest.raises(PosApiValidationError) as exc_info:
        client.bank_accounts.read("37900846788")
    assert exc_info.value.stage == "response"
    assert exc_info.value.model == "BankAccount"


@pytest.mark.asyncio
@respx.mock
async def test_bank_accounts_non_list_body_raises_sdk_validation_error() -> None:
    respx.get(f"{BASE_REST_URL}/rest/bankAccounts").mock(
        return_value=httpx.Response(200, json={"not": "a list"})
    )
    async with _client() as client:
        with pytest.raises(PosApiValidationError) as exc_info:
            await client.bank_accounts.aread("37900846788")
    assert exc_info.value.stage == "response"
    assert exc_info.value.model == "list[BankAccount]"


@respx.mock
def test_bank_accounts_business_error_body() -> None:
    respx.get(f"{BASE_REST_URL}/rest/bankAccounts").mock(
        return_value=httpx.Response(200, json=BUSINESS_ERROR_BODY)
    )
    with _client() as client, pytest.raises(PosApiBusinessError):
        client.bank_accounts.read("37900846788")


# --- #82 (1): malformed date must not mask the HTTP error ---------------------


@pytest.mark.parametrize("bad_date", ["not-a-date", 12345, "2026-13-45"])
@respx.mock
def test_http_error_with_malformed_date_still_raises_http_error(bad_date: object) -> None:
    respx.post(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(
            400, json={"status": "ERROR", "message": "bad request", "date": bad_date}
        )
    )
    with _client() as client, pytest.raises(PosApiHttpError) as exc_info:
        client.receipt.create(SUCCESS_REQUEST)
    err = exc_info.value
    assert err.date is None
    assert err.status == "ERROR"
    assert "bad request" in err.message


@respx.mock
def test_http_error_with_valid_date_is_parsed() -> None:
    respx.post(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(
            400, json={"status": "ERROR", "message": "x", "date": "2026-11-01T10:00:00"}
        )
    )
    with _client() as client, pytest.raises(PosApiHttpError) as exc_info:
        client.receipt.create(SUCCESS_REQUEST)
    assert exc_info.value.date is not None and exc_info.value.date.year == 2026


# --- no-response-model paths (receipt delete) --------------------------------


@respx.mock
def test_receipt_delete_non_json_200_body_is_tolerated() -> None:
    respx.delete(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(200, text="OK", headers={"content-type": "text/plain"})
    )
    with _client() as client:
        assert client.receipt.delete({"id": "037900846788001095330000010012619"}) is None


@respx.mock
def test_receipt_delete_business_error_body_raises() -> None:
    respx.delete(f"{BASE_REST_URL}/rest/receipt").mock(
        return_value=httpx.Response(200, json=BUSINESS_ERROR_BODY)
    )
    with _client() as client, pytest.raises(PosApiBusinessError):
        client.receipt.delete({"id": "037900846788001095330000010012619"})
