import datetime

import httpx
import pytest
import respx

from ebarimt_pos_sdk import (
    CreateReceiptRequest,
    DeleteReceiptRequest,
    EbarimtRestClient,
    Item,
    PosApiDecodeError,
    PosApiValidationError,
    RestClientSettings,
    SubReceipt,
)

from ..data.receipt import SUCCESS_RESPONSE
from ..helpers import BASE_REST_URL

create_receipt_payload = CreateReceiptRequest(
    branch_no="001",
    total_amount=1000,
    merchant_tin="12345678901",
    pos_no="001",
    type="B2C_RECEIPT",
    bill_id_suffix="01",
    receipts=[
        SubReceipt(
            total_amount=1000,
            tax_type="VAT_ABLE",
            merchant_tin="12345678901",
            items=[
                Item(
                    name="Bread",
                    bar_code="19059010880001",
                    measure_unit="senlovesfits",
                    qty=1,
                    unit_price=1000,
                    total_amount=1000,
                )
            ],
        )
    ],
)

delete_receipt_payload = DeleteReceiptRequest(
    id="1234567890123412319237123123",
    date=datetime.datetime.now(),
)
DECODE_ERROR_RECEIPT_SUCCESS_RESPONSE = httpx.Response(200, text="Decode error")


@pytest.mark.asyncio
@respx.mock
async def test_receipt_create_async_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
            200,
            json=SUCCESS_RESPONSE,
        )
    )

    async with EbarimtRestClient(settings) as client:
        payload = create_receipt_payload

        resp = await client.receipt.acreate(payload)
        assert resp.status == "SUCCESS"
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_receipt_delete_async_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.delete(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
            200,
            json={"status": "SUCCESS"},
        )
    )

    async with EbarimtRestClient(settings) as client:
        payload = DeleteReceiptRequest(
            id="1234567890123412319237123123",
            date=datetime.datetime.now(),
        )
        resp = await client.receipt.adelete(payload)
        assert resp is None
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_receipt_delete_async_empty_response_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.delete(f"{base_url}/rest/receipt").mock(return_value=httpx.Response(204))

    async with EbarimtRestClient(settings) as client:
        resp = await client.receipt.adelete(delete_receipt_payload)
        assert resp is None
        assert route.called


@respx.mock
def test_receipt_create_sync_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
            200,
            json=SUCCESS_RESPONSE,
        )
    )

    client = EbarimtRestClient(settings)

    payload = create_receipt_payload

    resp = client.receipt.create(payload)
    assert resp.status == "SUCCESS"
    assert route.called


@respx.mock
def test_receipt_create_sync_validation_error() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=DECODE_ERROR_RECEIPT_SUCCESS_RESPONSE
    )

    client = EbarimtRestClient(settings)

    payload = {
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

    with pytest.raises(PosApiValidationError):
        client.receipt.create(payload)
        assert route.called


@respx.mock
def test_receipt_create_sync_decode_error() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=DECODE_ERROR_RECEIPT_SUCCESS_RESPONSE
    )

    client = EbarimtRestClient(settings)

    payload = {
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

    with pytest.raises(PosApiDecodeError):
        client.receipt.create(payload)


@respx.mock
def test_receipt_delete_sync_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.delete(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
            200,
            json={"status": "SUCCESS"},
        )
    )

    with EbarimtRestClient(settings) as client:
        resp = client.receipt.delete(delete_receipt_payload)
        assert resp is None
        assert route.called


@respx.mock
def test_receipt_delete_sync_empty_response_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.delete(f"{base_url}/rest/receipt").mock(return_value=httpx.Response(200))

    with EbarimtRestClient(settings) as client:
        resp = client.receipt.delete(delete_receipt_payload)
        assert resp is None
        assert route.called
