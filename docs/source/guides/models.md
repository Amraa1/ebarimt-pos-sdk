# Models and validation

Requests and responses are [pydantic](https://docs.pydantic.dev/) v2 models. This page explains how they map to the JSON that PosAPI uses and what the SDK does and does not validate.

## Field names

PosAPI uses `camelCase` JSON names such as `merchantTin`. The models use `snake_case` attribute names such as `merchant_tin` and convert between the two.

Input accepts either spelling:

```python
from ebarimt_pos_sdk import Item

Item.model_validate(
    {"name": "Талх", "measureUnit": "ш", "qty": 1, "unitPrice": 5000, "totalAmount": 5000}
)
Item.model_validate(
    {"name": "Талх", "measure_unit": "ш", "qty": 1, "unit_price": 5000, "total_amount": 5000}
)
```

On responses you always read the `snake_case` attribute:

```python
receipt.total_amount
receipt.qr_data
```

To get the JSON form back, for example to store the response, dump the model by alias:

```python
receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
```

A few names do not follow the simple rule. The SDK handles them, you only see the `snake_case` name:

| Attribute | JSON name |
| --- | --- |
| `total_vat` | `totalVAT` |
| `terminal_id` | `terminalID` |
| `iban` | `iBan` |
| `operator_tin` | `operatorTIN` |

## Dictionaries or models

Methods that take a payload accept a model instance or a `dict`. A `dict` is validated against the model before anything is sent, so both forms get the same checks. Models give you editor completion and type checking; dictionaries are convenient when the data already comes from JSON.

## Enumerations

Fields with a fixed set of values accept the enum member or its string value.

| Enum | Values |
| --- | --- |
| `ReceiptType` | `B2C_RECEIPT`, `B2B_RECEIPT`, `B2C_INVOICE`, `B2B_INVOICE` |
| `TaxType` | `VAT_ABLE`, `VAT_FREE`, `VAT_ZERO`, `NO_VAT` |
| `BarCodeType` | `UNDEFINED`, `GS1`, `ISBN` |
| `PaymentCode` | `CASH`, `PAYMENT_CARD` |
| `PaymentStatus` | `PAID`, `PAY`, `REVERSED`, `ERROR` |
| `ReceiptCreateStatus` | `SUCCESS`, `ERROR`, `PAYMENT` |

## Amounts

Amount and quantity fields accept `int`, `float` or `decimal.Decimal`. Use `Decimal` or integers for money to avoid floating-point rounding.

## Dates

`CreateReceiptResponse.date` is parsed from PosAPI's `yyyy-MM-dd HH:mm:ss` text into a `datetime`. PosAPI sends no time zone. The SDK labels the value as UTC without shifting the clock time, so read the hour and minute as PosAPI reported them.

## What is validated

The SDK follows one rule: **validate structure, not policy**.

It checks:

- that required fields are present and have the right type;
- that enum fields hold one of the known values;
- simple numeric limits, such as `qty` and `unit_price` being greater than zero;
- that a sub-receipt has at least one item.

It does not check:

- business rules, such as which fields a receipt type requires;
- relations between fields, such as totals matching the sum of the items or the VAT amount;
- whether a TIN, district code or classification code exists.

The server owns those rules and can change them at any time. Keeping them out of the SDK means a rule change does not force you to upgrade.

A request that fails the structural checks raises `PosApiValidationError` before any network call. A request that the server rejects raises `PosApiBusinessError` or `PosApiHttpError`. See [](errors.md).

## Unknown fields

Models ignore fields they do not know.

For responses this means that existing code keeps working when PosAPI starts returning a new field. The field is not available on the model until the SDK adds it.

For requests it means that a key the model does not define is dropped and not sent. A misspelled optional field therefore does not raise an error. Building the request from model classes instead of a `dict` lets your editor and type checker catch such mistakes.
