import pytest

from ebarimt_pos_sdk import (
    CreateReceiptRequest,
    Item,
    PosApiClient,
    PosApiHttpError,
    PosApiSettings,
    Receipt,
)


@pytest.mark.integration
def test_integration_receipt_create_real_server():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

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
    with pytest.raises(PosApiHttpError):
        resp = client.receipt.create(payload)
        assert resp.status == "ERROR"
