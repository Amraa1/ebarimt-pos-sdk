# ebarimt-pos-sdk

[![codecov](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk/graph/badge.svg?token=EZ18HFDG46)](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

A modern, async-first Python SDK for the **Ebarimt POS API 3.0** — Mongolia's electronic receipting (e-баримт) platform.
It wraps both the public OAuth2 API and the local REST API exposed by POS devices behind a single, typed, ergonomic
interface.

> 📖 Full documentation: <https://ebarimt-pos-sdk.readthedocs.io/mn/latest/> 📘 Ebarimt POS API 3.0 reference:
> <https://developer.itc.gov.mn/docs/ebarimt-api/inbishdm2zj3x-pos-api-3-0-sistemijn-api-holbolt-zaavruud> 🇲🇳 Mongolian
> version of this README: [README_MN.md](./README_MN.md)

---

## Features

- **Async-first** — every operation exposes both a synchronous and an `async` variant (`method()` / `amethod()`), built
  on `httpx`.
- **Strictly typed** — Pydantic v2 models with camelCase ↔ snake_case aliasing; full `mypy --strict` compliance.
- **Two focused clients** — `EbarimtApiClient` for the public OAuth2 API, `EbarimtRestClient` for the local POS REST
  API.
- **Managed OAuth2** — built-in password-grant flow with automatic token refresh and proactive expiry handling.
- **Resilient transport** — configurable retry with exponential backoff on 5xx and network errors, per-request timeouts,
  and TLS verification.
- **Structured errors** — a clear exception hierarchy distinguishing transport, HTTP, decode, validation, and business
  failures. Sensitive headers and tokens are automatically redacted from error output.
- **Environment presets** — one-line switch between `STAGING` and `PRODUCTION` endpoints via `create_api_settings`.

---

## Installation

```bash
pip install ebarimt-pos-sdk
```

Or with `uv`:

```bash
uv add ebarimt-pos-sdk
```

Requires Python 3.10 or newer.

---

## Quick Start

### Local REST client — issue a receipt

```python
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

settings = RestClientSettings(base_url="http://localhost:1234")

with EbarimtRestClient(settings) as client:
    receipt = client.receipt.create({
        "branch_no": "001",
        "total_amount": 10000,
        "merchant_tin": "1234567890",
        "pos_no": "POS001",
        "type": "B2C_RECEIPT",
        "bill_id_suffix": "A",
        "receipts": [{
            "total_amount": 10000,
            "tax_type": "VAT_ABLE",
            "merchant_tin": "1234567890",
            "items": [{
                "name": "Product",
                "measure_unit": "ш",
                "qty": 1,
                "unit_price": 10000,
                "total_amount": 10000,
            }],
        }],
    })
    print(receipt.id, receipt.qr_data)
```

Async variant: swap `with` for `async with` and call `await client.receipt.acreate(...)`.

```python
import asyncio
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

async def main() -> None:
    async with EbarimtRestClient(RestClientSettings(base_url="http://localhost:1234")) as client:
        receipt = await client.receipt.acreate(payload)
        print(receipt.id)

asyncio.run(main())
```

### Public API client — look up a TIN

Use the factory to target a specific environment without hard-coding URLs:

```python
from ebarimt_pos_sdk import (
    EbarimtApiClient,
    Environment,
    create_api_settings,
)

settings = create_api_settings(
    Environment.PRODUCTION,  # or Environment.STAGING
    client_id="your_client_id",
    username="your_username",
    password="your_password",
)

with EbarimtApiClient(settings=settings) as client:
    info = client.tin_info.read("1234567890")
    print(info.data)
```

---

## Clients at a glance

| Client              | Authentication        | Available resources                                              |
| ------------------- | --------------------- | ---------------------------------------------------------------- |
| `EbarimtRestClient` | None (local network)  | `receipt`, `info`, `send_data`, `bank_accounts`                  |
| `EbarimtApiClient`  | OAuth2 password grant | `district_code`, `tin_info`, `merchant_info`, `product_tax_code` |

Both clients support synchronous and asynchronous context managers, share a common settings base (timeouts, TLS,
headers, retry policy), and reuse the same error hierarchy.

---

## Error handling

The SDK surfaces failures through a focused exception hierarchy, so you can react at the level of abstraction that
matters to your code:

```text
PosApiError
├── PosApiTransportError    # network / timeout / DNS / TLS
├── PosApiDecodeError       # response body was not valid JSON
├── PosApiHttpError         # non-2xx response from server
├── PosApiBusinessError     # 2xx, but domain-level failure in payload
└── PosApiValidationError   # Pydantic validation of request or response
```

```python
from ebarimt_pos_sdk import (
    PosApiBusinessError,
    PosApiHttpError,
    PosApiTransportError,
    PosApiValidationError,
)

try:
    receipt = client.receipt.create(payload)
except PosApiValidationError as e:
    # Bad shape — fix the request before resending
    for err in e.errors:
        print(err["loc"], err["msg"])
except PosApiBusinessError as e:
    # Server accepted the request but rejected it on business grounds
    print(e.status, e.code, e.message)
except PosApiHttpError as e:
    # 4xx / 5xx — includes safe, redacted request/response context
    print(e)
except PosApiTransportError:
    # Network layer — safe to retry later
    raise
```

`Authorization` headers and token-bearing query parameters are redacted automatically in every error's string
representation.

---

## Configuration

All settings are immutable dataclasses — construct once and pass to the client. Timeouts, TLS verification, custom
headers, and retry behaviour are shared across both clients via `BaseSettings`.

```python
from ebarimt_pos_sdk import RestClientSettings
from ebarimt_pos_sdk.settings import RetrySettings

settings = RestClientSettings(
    base_url="http://localhost:1234",
    timeout_s=5.0,
    verify_tls=True,
    headers={"X-Request-Source": "pos-42"},
    retry=RetrySettings(
        max_retries=3,
        backoff_base_seconds=1.0,
        retryable_statuses=frozenset({500, 502, 503, 504}),
    ),
)
```

The default retry policy — 3 attempts with exponential backoff on 5xx and network errors — is suitable for most
deployments.

---

## Validation philosophy

The SDK validates **structure, not policy**:

- ✅ Field shapes, regex for stable identifiers (TIN, branch codes), enums, and basic numeric constraints (`>= 0`).
- ❌ Business rules, cross-field dependencies, reference-table lookups, or any government policy that changes out of
  band.

This boundary is intentional. The server owns business rules; the SDK owns shape correctness. That keeps the SDK stable
when rules change.

---

## Development

```bash
# Install all dependencies, including dev extras
uv sync --dev

# Run the unit test suite
uv run pytest -m "not integration"

# Run with coverage
uv run pytest -m "not integration" --cov

# Lint and format
uv run ruff check
uv run ruff format

# Type check (strict)
uv run mypy src
```

Integration tests (marked `@pytest.mark.integration`) require a live PosAPI server and credentials; they are excluded
from CI by default.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines and [CHANGELOG.md](./CHANGELOG.md) for release
notes.

---

## License

Released under the [MIT License](./LICENSE).
