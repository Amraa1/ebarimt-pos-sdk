import pytest

from ebarimt_pos_sdk import (
    CreateReceiptRequest,
    Item,
    EbarimtRestClient,
    PosApiHttpError,
    RestClientSettings,
    Receipt,
)


@pytest.mark.integration
def test_integration_receipt_create_real_server():
    base_url = "http://localhost:7080"
    settings = RestClientSettings(base_url=base_url)

    client = EbarimtRestClient(settings)

    payload = CreateReceiptRequest(
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
    with pytest.raises(PosApiHttpError):
        resp = client.receipt.create(payload)
        assert resp.status == "ERROR"
