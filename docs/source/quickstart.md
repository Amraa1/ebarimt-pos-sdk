# Quickstart

This page issues a receipt, cancels it, and looks up a taxpayer. Each step is explained in more detail in the guides.

## Issue a receipt

Create a client that points at your PosAPI service and call `receipt.create()`.

```python
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

settings = RestClientSettings(base_url="http://localhost:7080")

with EbarimtRestClient(settings) as client:
    receipt = client.receipt.create(
        {
            "branch_no": "001",
            "total_amount": 11000,
            "total_vat": 1000,
            "merchant_tin": "37900846788",
            "pos_no": "001",
            "district_code": "2501",
            "type": "B2C_RECEIPT",
            "bill_id_suffix": "01",
            "receipts": [
                {
                    "total_amount": 11000,
                    "total_vat": 1000,
                    "tax_type": "VAT_ABLE",
                    "merchant_tin": "37900846788",
                    "items": [
                        {
                            "name": "Талх",
                            "bar_code": "19059010880001",
                            "bar_code_type": "GS1",
                            "classification_code": "2349010",
                            "measure_unit": "ш",
                            "qty": 1,
                            "unit_price": 11000,
                            "total_amount": 11000,
                            "total_vat": 1000,
                        }
                    ],
                }
            ],
            "payments": [{"code": "CASH", "status": "PAID", "paid_amount": 11000}],
        }
    )

print(receipt.id)  # receipt number (ДДТД)
print(receipt.lottery)  # lottery number, if one was issued
print(receipt.qr_data)  # text to encode in the printed QR code
```

The identifiers and amounts above are sample values. Use the values registered for your own merchant and POS.

The payload can be a plain `dict` as shown, or a `CreateReceiptRequest` model. Field names are written in `snake_case`; the SDK converts them to the `camelCase` names PosAPI expects. See [](guides/models.md).

## Cancel a receipt

```python
client.receipt.delete({"id": receipt.id, "date": receipt.date})
```

## The same thing with asyncio

Use `async with` and the `a`-prefixed methods.

```python
import asyncio

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings


async def main() -> None:
    settings = RestClientSettings(base_url="http://localhost:7080")
    async with EbarimtRestClient(settings) as client:
        info = await client.info.aread()
        print(info.pos_no)


asyncio.run(main())
```

## Look up a taxpayer

`EbarimtApiClient` talks to the public Ebarimt API. `create_api_settings` fills in the URLs for the environment you choose.

```python
from ebarimt_pos_sdk import EbarimtApiClient, Environment, create_api_settings

settings = create_api_settings(Environment.PRODUCTION)

with EbarimtApiClient(settings) as client:
    tin = client.tin_info.read("УБ12345678").data  # registration number -> TIN
    merchant = client.merchant_info.read(tin).data

    if merchant is not None:
        print(merchant.name, merchant.vat_payer)
```

## Handle failures

Every error raised by the SDK derives from `PosApiError`.

```python
from ebarimt_pos_sdk import PosApiError

try:
    receipt = client.receipt.create(payload)
except PosApiError as error:
    print(error)
```

A failed `receipt.create()` needs more care than this, because resending it blindly can issue a second receipt. [](guides/errors.md) explains how to tell the safe cases from the unsafe ones.
