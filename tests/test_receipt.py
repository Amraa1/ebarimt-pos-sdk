import datetime

import httpx
import pytest
import respx

from ebarimt_pos_sdk import (
    CreateReceiptRequest,
    DeleteReceiptRequest,
    Item,
    PosApiClient,
    PosApiDecodeError,
    PosApiSettings,
    PosApiValidationError,
    Receipt,
)

CREATE_RECEIPT_SUCCESS_RESPONSE = httpx.Response(
    200,
    json={
        "id": "1" * 33,
        "posId": 1,
        "status": "SUCCESS",
        "message": "OK",
        "qrDate": "qr",
        "lottery": "lot",
        "date": "2026-01-27",
        "easy": "true",
        "receipts": [{"id": "sub1", "bankAccountId": 10}],
    },
)


DECODE_ERROR_RECEIPT_SUCCESS_RESPONSE = httpx.Response(200, text="Decode error")


@pytest.mark.asyncio
@respx.mock
async def test_receipt_create_async_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=CREATE_RECEIPT_SUCCESS_RESPONSE
    )

    async with PosApiClient(settings) as client:
        payload = CreateReceiptRequest(
            branchNo="001",
            totalAmount=1000,
            merchantTin="12345678901",
            posNo="001",
            type="B2C_RECEIPT",
            billIdSuffix="01",
            receipts=[
                Receipt(
                    totalAmount=1000,
                    taxType="VAT_ABLE",
                    merchantTin="12345678901",
                    items=[
                        Item(
                            name="Bread",
                            barCode="19059010880001",
                            measureUnit="senlovesfits",
                            qty=1,
                            unitPrice=1000,
                            totalAmount=1000,
                        )
                    ],
                )
            ],
        )

        resp = await client.receipt.acreate(payload)
        assert resp.status == "SUCCESS"
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_receipt_delete_async_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
            200,
            json={"status": "SUCCESS"},
        )
    )

    async with PosApiClient(settings) as client:
        payload = DeleteReceiptRequest(
            id="1234567890123412319237123123", date=datetime.datetime.now()
        )

        await client.receipt.adelete(payload)
        assert route.called


@respx.mock
def test_receipt_create_sync_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=CREATE_RECEIPT_SUCCESS_RESPONSE
    )

    client = PosApiClient(settings)

    payload = CreateReceiptRequest(
        branchNo="001",
        totalAmount=1000,
        merchantTin="12345678901",
        posNo="001",
        type="B2C_RECEIPT",
        billIdSuffix="01",
        receipts=[
            Receipt(
                totalAmount=1000,
                taxType="VAT_ABLE",
                merchantTin="12345678901",
                items=[
                    Item(
                        name="Bread",
                        barCode="19059010880001",
                        measureUnit="senlovesfits",
                        qty=1,
                        unitPrice=1000,
                        totalAmount=1000,
                    )
                ],
            )
        ],
    )

    resp = client.receipt.create(payload)
    assert resp.status == "SUCCESS"
    assert route.called


@respx.mock
def test_receipt_create_sync_validation_error():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=DECODE_ERROR_RECEIPT_SUCCESS_RESPONSE
    )

    client = PosApiClient(settings)

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


@respx.mock
def test_receipt_create_sync_decode_error():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=DECODE_ERROR_RECEIPT_SUCCESS_RESPONSE
    )

    client = PosApiClient(settings)

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
def test_receipt_delete_sync_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
            200,
            json={"status": "SUCCESS"},
        )
    )

    with PosApiClient(settings) as client:
        payload = DeleteReceiptRequest(
            id="1234567890123412319237123123", date=datetime.datetime.now()
        )

        client.receipt.delete(payload)
        assert route.called
