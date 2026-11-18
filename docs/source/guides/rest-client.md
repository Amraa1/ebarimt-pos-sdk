# Local REST client

`EbarimtRestClient` wraps the REST interface of the PosAPI service that runs on your POS machine or local network. It needs no authentication.

```python
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

client = EbarimtRestClient(RestClientSettings(base_url="http://localhost:7080"))
```

| Attribute | Method | HTTP request | Returns |
| --- | --- | --- | --- |
| `client.receipt` | `create(payload)` | `POST /rest/receipt` | `CreateReceiptResponse` |
| `client.receipt` | `delete(payload)` | `DELETE /rest/receipt` | `None` |
| `client.info` | `read()` | `GET /rest/info` | `ReadInfoResponse` |
| `client.send_data` | `send()` | `GET /rest/sendData` | `None` |
| `client.bank_accounts` | `read(tin)` | `GET /rest/bankAccounts` | `list[BankAccount]` |

Each method has an async twin: `acreate`, `adelete`, `aread`, `asend`.

## Client lifecycle

The client owns a connection pool. Close it when you are done, or use it as a context manager so that it is closed for you.

```python
with EbarimtRestClient(settings) as client:
    ...

async with EbarimtRestClient(settings) as client:
    ...
```

Without a context manager, call `client.close()` for synchronous use and `await client.aclose()` for asynchronous use.

Create one client and reuse it for the lifetime of your application. Creating a client for every request throws away the connection pool.

## Issuing a receipt

`receipt.create()` takes a `CreateReceiptRequest` or a `dict` with the same fields, and returns a `CreateReceiptResponse`.

```python
from ebarimt_pos_sdk import (
    CreateReceiptRequest,
    Item,
    Payment,
    PaymentCode,
    PaymentStatus,
    ReceiptType,
    SubReceipt,
    TaxType,
)

request = CreateReceiptRequest(
    branch_no="001",
    total_amount=11000,
    total_vat=1000,
    merchant_tin="37900846788",
    pos_no="001",
    district_code="2501",
    type=ReceiptType.B2C_RECEIPT,
    bill_id_suffix="01",
    receipts=[
        SubReceipt(
            total_amount=11000,
            total_vat=1000,
            tax_type=TaxType.VAT_ABLE,
            merchant_tin="37900846788",
            items=[
                Item(
                    name="Талх",
                    measure_unit="ш",
                    qty=1,
                    unit_price=11000,
                    total_amount=11000,
                    total_vat=1000,
                )
            ],
        )
    ],
    payments=[
        Payment(code=PaymentCode.CASH, status=PaymentStatus.PAID, paid_amount=11000),
    ],
)

receipt = client.receipt.create(request)
```

A receipt contains one or more sub-receipts (`receipts`). Each sub-receipt has one tax type and one seller, and lists its items. A sale that mixes taxable and tax-free goods therefore has two sub-receipts.

The fields you will use most from the response:

| Field | Meaning |
| --- | --- |
| `id` | Receipt number (ДДТД). Keep it: you need it to cancel the receipt. |
| `date` | Time the receipt was created. Also needed to cancel it. |
| `qr_data` | Text to encode in the QR code printed on the receipt. |
| `lottery` | Lottery number. `None` when the response contains no lottery number. |
| `status` | `SUCCESS`, `ERROR` or `PAYMENT`. |
| `receipts` | The sub-receipts, each with its own `id`. |

The SDK checks the shape of the request before sending it: required fields, types, enum values, a positive `qty` and `unit_price`, and at least one item per sub-receipt. It does not check totals, tax calculations or any other rule of the e-barimt system. PosAPI does that and its verdict is reported as an error, see [](errors.md).

```{note}
The PosAPI specification forbids storing `lottery` and `qr_data` in any form other than printing them on the receipt.
```

```{warning}
`receipt.create()` is never retried automatically. If it fails with a network error, the receipt may already exist. Read [](errors.md#avoiding-duplicate-receipts) before adding your own retry.
```

## Cancelling a receipt

Pass the `id` of the receipt and the `date` it was created.

```python
from ebarimt_pos_sdk import DeleteReceiptRequest

client.receipt.delete(DeleteReceiptRequest(id=receipt.id, date=receipt.date))
```

`date` is a `datetime`. The SDK sends it in the `yyyy-MM-dd HH:mm:ss` format PosAPI expects. The method returns `None` and raises an error if PosAPI rejects the cancellation.

## Reading PosAPI status

`info.read()` returns the configuration and state of the PosAPI instance.

```python
info = client.info.read()

print(info.operator_name, info.pos_no)
print(info.last_sent_date)  # last time receipts were sent to the central system
print(info.left_lotteries)  # lottery numbers still available

for merchant in info.merchants:
    print(merchant.tin, merchant.name)
```

`left_lotteries` and `last_sent_date` are worth monitoring: they show whether the instance is running out of lottery numbers and whether it is still uploading receipts.

## Sending receipts to the central system

`send_data.send()` asks PosAPI to send its stored receipts to the central e-barimt system now. PosAPI also refreshes its bank account list during this operation.

```python
client.send_data.send()
```

## Listing bank accounts

`bank_accounts.read()` returns the bank accounts that PosAPI has registered for a taxpayer.

```python
for account in client.bank_accounts.read("37900846788"):
    print(account.bank_name, account.bank_account_no, account.iban)
```

## Per-request headers

Every method accepts a `headers` keyword argument. The headers are added to that one request and override client-level headers with the same name.

```python
client.info.read(headers={"X-Request-Source": "pos-42"})
```

To send a header with every request, pass `headers` to the client constructor, see [](configuration.md#default-headers).
