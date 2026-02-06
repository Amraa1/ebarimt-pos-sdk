import datetime

import httpx
import respx

from ebarimt_pos_sdk import (
    CreateReceiptRequest,
    DeleteReceiptRequest,
    Item,
    PosApiClient,
    PosApiSettings,
    Receipt,
)


@respx.mock
def test_receipt_create_sync_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.post(f"{base_url}/rest/receipt").mock(
        return_value=httpx.Response(
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
