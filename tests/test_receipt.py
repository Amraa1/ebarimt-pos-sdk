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
    ReceiptType,
    Receipt,
)

CREATE_RECEIPT_SUCCESS_RESPONSE = httpx.Response(
    200,
    json={
    "id": "037900846788001095330000010012619",
    "version": "3.2.39",
    "totalAmount": 5600,
    "totalVAT": 500,
    "totalCityTax": 100,
    "branchNo": "001",
    "districtCode": "2501",
    "merchantTin": "37900846788",
    "posNo": "001",
    "consumerNo": "10038071",
    "type": "B2C_RECEIPT",
    "receipts": [
        {
            "id": "037900846788001095330000110012619",
            "totalAmount": 5600,
            "taxType": "VAT_ABLE",
            "items": [
                {
                    "name": "Талх",
                    "barCode": "19059010880001",
                    "barCodeType": "GS1",
                    "classificationCode": "2349010",
                    "measureUnit": "senlovesfits",
                    "qty": 1,
                    "unitPrice": 5000,
                    "totalAmount": 5600,
                    "totalVAT": 500,
                    "totalCityTax": 100
                }
            ],
            "merchantTin": "37900846788",
            "totalVAT": 500,
            "totalCityTax": 100
        }
    ],
    "payments": [
        {
            "code": "CASH",
            "paidAmount": 5600,
            "status": "PAID"
        }
    ],
    "posId": 101321077,
    "status": "SUCCESS",
    "qrData": "30892326524546672474592603677629267669202520788666570091176582304861979527775302772692166239698276252024697295297031948644121173043640072110272573911246153670156937219597386482037042663801023934072070",
    "lottery": "SN 47461258",
    "date": "2026-02-12 15:31:42",
    "easy": True,
    }
)

create_receipt_payload = CreateReceiptRequest(
        branch_no="001",
        total_amount=1000,
        merchant_tin="12345678901",
        pos_no="001",
        type="B2C_RECEIPT",
        bill_id_suffix="01",
        receipts=[
            Receipt(
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
            id="1234567890123412319237123123", date=datetime.datetime.now(), type=ReceiptType.B2C_RECEIPT
        )

DECODE_ERROR_RECEIPT_SUCCESS_RESPONSE = httpx.Response(200, text="Decode error")


@pytest.mark.asyncio
@respx.mock
async def test_receipt_create_async_ok() -> None:
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=CREATE_RECEIPT_SUCCESS_RESPONSE
    )

    async with PosApiClient(settings) as client:
        payload = create_receipt_payload

        resp = await client.receipt.acreate(payload)
        assert resp.status == "SUCCESS"
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_receipt_delete_async_ok() -> None:
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
            id="1234567890123412319237123123", date=datetime.datetime.now(), type=ReceiptType.B2C_RECEIPT
        )

        await client.receipt.adelete(payload)
        assert route.called


@respx.mock
def test_receipt_create_sync_ok() -> None:
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=CREATE_RECEIPT_SUCCESS_RESPONSE
    )

    client = PosApiClient(settings)

    payload = create_receipt_payload

    resp = client.receipt.create(payload)
    assert resp.status == "SUCCESS"
    assert route.called


@respx.mock
def test_receipt_create_sync_validation_error() -> None:
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
def test_receipt_create_sync_decode_error() -> None:
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
def test_receipt_delete_sync_ok() -> None:
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
            200,
            json={"status": "SUCCESS"},
        )
    )

    with PosApiClient(settings) as client:
        payload = delete_receipt_payload

        client.receipt.delete(payload)
        assert route.called
