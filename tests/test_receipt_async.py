import httpx
import pytest
import respx

from ebarimt_pos_sdk import PosApiClient, PosApiSettings


@pytest.mark.asyncio
@respx.mock
async def test_receipt_create_async_ok():
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

    async with PosApiClient(settings) as client:
        payload = {
            "branchNo": "001",
            "totalAmount": 1000,
            "merchantTin": "12345678901",
            "posNo": "001",
            "type": "B2C_RECEIPT",
            "billIdSuffix": "01",
            "receipts": [{"items": [{"name": "x"}]}],
            "payments": [{"code": "CASH", "status": "PAID", "paidAmount": 1000}],
        }

        resp = await client.receipt.acreate(payload)
        assert resp.status == "SUCCESS"
        assert route.called
