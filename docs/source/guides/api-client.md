# Public API client

`EbarimtApiClient` wraps the lookup endpoints of the public Ebarimt API. They return reference data that you need to fill in a receipt correctly.

```python
from ebarimt_pos_sdk import EbarimtApiClient, Environment, create_api_settings

client = EbarimtApiClient(create_api_settings(Environment.PRODUCTION))
```

| Attribute | Method | Returns |
| --- | --- | --- |
| `client.tin_info` | `read(reg_no)` | The TIN for a registration number |
| `client.merchant_info` | `read(tin)` | Name and tax status of a taxpayer |
| `client.district_code` | `read()` | All district (branch) codes |
| `client.product_tax_code` | `read()` | Product codes for tax-free and zero-rated goods |
| `client.buna` | `read(*segments)` | One level of the BUNA classification |
| `client.merchant_registration` | `create(payload)` | Acknowledgement of a merchant registration request |

Each method has an async twin with an `a` prefix (`aread`, `acreate`). The client lifecycle is the same as for the REST client: use `with` / `async with`, or call `close()` / `aclose()`.

## Environments

`create_api_settings` returns settings for one of two environments.

| Environment | Base URL |
| --- | --- |
| `Environment.PRODUCTION` | `https://api.ebarimt.mn` |
| `Environment.STAGING` | `https://st-api.ebarimt.mn` |

To use another URL, build the settings yourself:

```python
from ebarimt_pos_sdk import ApiClientSettings

settings = ApiClientSettings(base_url="https://api.example.mn")
```

## Authentication

The lookup endpoints are public. The client does not request or send a token for them, even when the settings contain credentials.

Only `merchant_registration` needs credentials: an OAuth2 password-grant token and an API key. Pass them to `create_api_settings`, which fills in the token URL for the environment:

```python
settings = create_api_settings(
    Environment.STAGING,
    client_id="your_client_id",
    username="your_username",
    password="your_password",
    api_key="your_api_key",  # sent as X-API-KEY
)
```

`client_secret` and `scope` are optional. The token is fetched on first use, reused until it expires and renewed once if the server rejects it. The token request goes through the same HTTP client as every other request, so it uses the same proxy, TLS and timeout settings. `password`, `client_secret` and `api_key` are hidden from the settings object's `repr()`, and the token and API key are masked in logs and error messages.

Calling `merchant_registration` without one of `token_url`, `client_id`, `username`, `password` or `api_key` raises `PosApiConfigurationError` before anything is sent. Its message lists the missing fields.

## Looking up a taxpayer

Receipts identify buyers and sellers by TIN (ТТД). `tin_info.read()` converts a registration number into a TIN, and `merchant_info.read()` returns the details for a TIN.

```python
tin = client.tin_info.read("УБ12345678").data

response = client.merchant_info.read(tin)
merchant = response.data

if merchant is None or not merchant.found:
    print("Unknown taxpayer")
else:
    print(merchant.name)
    print("VAT payer:", merchant.vat_payer)
    print("City tax payer:", merchant.city_payer)
```

`data` is `None` when the server does not know the TIN, so check it before use. `vatpayer_registered_date` and `is_government` can also be `None`.

## District codes

The `district_code` field of a receipt says where the sale took place. `district_code.read()` returns the list of tax offices (`branch_code`) and their sub-offices (`sub_branch_code`). The two codes joined together form the value, for example `0102`.

```python
for branch in client.district_code.read().data:
    print(branch.branch_code, branch.branch_name, branch.sub_branch_code, branch.sub_branch_name)
```

## Product tax codes

An item that is exempt from VAT or zero-rated carries a `tax_product_code` that names the legal basis. `product_tax_code.read()` returns the list of valid codes.

```python
for code in client.product_tax_code.read().data:
    print(code.tax_product_code, code.tax_type_name.value, code.tax_product_name)
```

This list and the district list change rarely. Cache them instead of fetching them for every receipt.

## BUNA classification

The `classification_code` of a receipt item comes from the BUNA classification of goods and services (БҮНА). The classification is a tree. `buna.read()` returns one level of it, and you go deeper by passing the code chosen at each level.

```python
sectors = client.buna.read()  # top level
sub_sectors = client.buna.read("0")  # children of sector "0"
groups = client.buna.read("0", "01")  # children of "01"

for code, name in sectors.root:
    print(code, name)
```

The levels, from the top, are sector, sub-sector, group, class, sub-class and BUNA code. A seventh call with all six codes returns the barcodes registered under that BUNA code.

The response is a list of rows and each row is a list of strings. Classification rows are `[code, name]`. Barcode rows are `[barcode, name, registered_date]`. The rows are available as `response.root`.

## Registering merchants

An operator adds merchants to its POS with `merchant_registration.create()`. This replaces the manual step in the operator portal (operator.ebarimt.mn).

```python
from ebarimt_pos_sdk import CreateMerchantRegistrationRequest

response = client.merchant_registration.create(
    CreateMerchantRegistrationRequest(pos_no="10005299", merchant_tins=["77001059076"])
)
print(response.msg)
```

The call only submits a request. eBarimt approves it later, and there is no endpoint that reports the status of a request. To find out when a merchant is approved, poll the local POS with `EbarimtRestClient.info.read()` until the merchant's TIN appears in its merchant list.

`pos_no` must not be empty and every TIN must have 11 digits. If eBarimt refuses the request, the call raises `PosApiBusinessError` with eBarimt's `msg` as the message and its `status` and `code` attached. The SDK does not interpret the refusal: whether "already registered" is acceptable is for your code to decide.

The request is a `POST`, so it is never resent after it may have reached the server. See [](errors.md) for how to handle a failed call.

## Using a proxy

The public API may refuse connections from outside Mongolia. If your server is elsewhere, send the requests through a proxy located in Mongolia.

```python
client = EbarimtApiClient(settings, proxy="http://user:password@proxy.example.mn:8080")
```

`proxy` accepts a URL or an `httpx.Proxy` object. SOCKS proxies need the `httpx[socks]` extra. If you pass your own `httpx` client to the constructor, configure the proxy on that client instead: combining `proxy` with `sync_client` or `async_client` raises `ValueError`.

`EbarimtRestClient` has no `proxy` argument because it talks to a service on your own network.
