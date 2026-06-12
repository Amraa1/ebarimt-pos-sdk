import pytest

from ebarimt_pos_sdk import (
    CreateReceiptRequest,
    DeleteReceiptRequest,
    EbarimtApiClient,
    EbarimtRestClient,
    Environment,
    Item,
    Payment,
    PosApiHttpError,
    RestClientSettings,
    SubReceipt,
    create_api_settings,
)

from ..helpers import BASE_REST_URL, TIN

# Registration number of the customer organization used in the B2B receipt test.
B2B_CUSTOMER_REG_NO = "1122334"


@pytest.mark.integration
def test_integration_receipt_create_real_server():
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    client = EbarimtRestClient(settings)

    payload = CreateReceiptRequest(
        branch_no="001",
        total_amount=1000,
        merchant_tin=TIN,
        pos_no="001",
        type="B2C_RECEIPT",
        bill_id_suffix="01",
        receipts=[
            SubReceipt(
                total_amount=1000,
                tax_type="VAT_ABLE",
                merchant_tin=TIN,
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


@pytest.mark.integration
def test_integration_receipt_delete_real_server():
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    client = EbarimtRestClient(settings)

    payload = CreateReceiptRequest(
        branch_no="001",
        total_amount=1100,
        total_vat=100,
        merchant_tin=TIN,
        district_code="2501",
        pos_no="001",
        type="B2C_RECEIPT",
        bill_id_suffix="01",
        receipts=[
            SubReceipt(
                total_amount=1100,
                total_vat=100,
                tax_type="VAT_ABLE",
                merchant_tin=TIN,
                items=[
                    Item(
                        name="Bread",
                        bar_code="19059010880001",
                        bar_code_type="GS1",
                        measure_unit="senlovesfits",
                        classification_code="2349010",
                        qty=1,
                        unit_price=1000,
                        total_amount=1100,
                        total_vat=100,
                    )
                ],
            )
        ],
        payments=[
            Payment(
                code="CASH",
                status="PAID",
                paid_amount=1100,
            )
        ],
    )
    resp = client.receipt.create(payload)
    assert resp.status == "SUCCESS"

    resp = client.receipt.delete(
        DeleteReceiptRequest(
            id=resp.id,
            date=resp.date,
        )
    )

    assert resp is None


@pytest.mark.integration
def test_integration_receipt_create_b2b_real_server():
    # B2B receipts need the customer's TIN; resolve it from the registration
    # number via the public info API first. Staging doesn't know every real
    # reg number, so fall back to production for the lookup only.
    customer_tin: str | None = None
    for env in (Environment.STAGING, Environment.PRODUCTION):
        with EbarimtApiClient(create_api_settings(env)) as api_client:
            tin_resp = api_client.tin_info.read(B2B_CUSTOMER_REG_NO)
        if tin_resp.status == 200 and tin_resp.data.isdigit():
            customer_tin = tin_resp.data
            break

    if customer_tin is None:
        pytest.skip(f"reg no {B2B_CUSTOMER_REG_NO} did not resolve to a TIN on any server")

    settings = RestClientSettings(base_url=BASE_REST_URL)
    client = EbarimtRestClient(settings)

    payload = CreateReceiptRequest(
        branch_no="001",
        total_amount=1100,
        total_vat=100,
        merchant_tin=TIN,
        customer_tin=customer_tin,
        district_code="2501",
        pos_no="001",
        type="B2B_RECEIPT",
        bill_id_suffix="01",
        receipts=[
            SubReceipt(
                total_amount=1100,
                total_vat=100,
                tax_type="VAT_ABLE",
                merchant_tin=TIN,
                customer_tin=customer_tin,
                items=[
                    Item(
                        name="Bread",
                        bar_code="19059010880001",
                        bar_code_type="GS1",
                        measure_unit="senlovesfits",
                        classification_code="2349010",
                        qty=1,
                        unit_price=1000,
                        total_amount=1100,
                        total_vat=100,
                    )
                ],
            )
        ],
        payments=[
            Payment(
                code="CASH",
                status="PAID",
                paid_amount=1100,
            )
        ],
    )
    resp = client.receipt.create(payload)
    assert resp.status == "SUCCESS"
    assert resp.type == "B2B_RECEIPT"
    assert resp.customer_tin == customer_tin

    # Clean up so the staging merchant isn't left with a dangling B2B receipt.
    delete_resp = client.receipt.delete(
        DeleteReceiptRequest(
            id=resp.id,
            date=resp.date,
        )
    )
    assert delete_resp is None
