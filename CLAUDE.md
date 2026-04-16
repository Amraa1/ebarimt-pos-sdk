# CLAUDE.md

This file provides guidance to Claude Code when working with the **ebarimt-pos-sdk** codebase.

## Project Overview

**ebarimt-pos-sdk** is an async-first Python SDK for the Ebarimt POS API 3.0 — Mongolia's electronic receipting (e-баримт) system. It wraps both the public OAuth2-protected API and the local REST API used by point-of-sale devices.

Core design philosophy: **"Validate structure, not policy."** The SDK validates JSON shape and format strictly, but deliberately avoids implementing government business rules (which change frequently and belong server-side).

## Tech Stack

- **Python 3.10+** — primary language; strict typing enforced
- **httpx** — async/sync HTTP client
- **pydantic v2** — data validation and serialization
- **authlib** — OAuth2 password grant flow
- **uv** — package manager and build tool (replaces pip/venv)
- **pytest + pytest-asyncio + respx** — testing
- **ruff** — linting and formatting
- **mypy** — static type checking (strict mode)
- **Sphinx** — documentation generation

## Key Commands

```bash
# Install all dependencies (including dev)
uv sync --dev

# Run unit tests (excluding integration)
uv run pytest -m "not integration"

# Run all tests with coverage
uv run pytest -m "not integration" --cov

# Lint
uv run ruff check

# Format
uv run ruff format

# Type check
uv run mypy src

# OpenAPI spec validation (requires Node.js)
npm run spec:check

# Build documentation
cd docs && make html
```

## Project Structure

```bash
src/ebarimt_pos_sdk/
├── __init__.py               # Public API exports
├── _types.py                 # Type aliases
├── errors.py                 # Exception hierarchy
├── factory.py                # Environment/settings factory
├── auth/                     # OAuth2 (password grant, token management)
├── clients/
│   ├── base_client.py        # Lifecycle, context managers
│   ├── api_client.py         # EbarimtApiClient — public API (OAuth2)
│   └── rest_client.py        # EbarimtRestClient — local POS REST API
├── resources/
│   ├── base_model.py         # Pydantic base with camelCase aliases
│   ├── base_resource.py      # Abstract resource base (sync + async)
│   ├── enum.py               # ReceiptType, PaymentCode, etc.
│   ├── api/                  # OAuth2-protected resources
│   │   ├── info/             # District codes, TIN info
│   │   ├── merchant/         # Merchant information
│   │   └── product/          # Product tax codes
│   └── rest/                 # Local POS resources
│       ├── receipt/          # Receipt create/delete
│       ├── info/             # Info endpoint
│       ├── send_data/        # Send data
│       └── bank_accounts/    # Bank accounts
├── settings/                 # Configuration dataclasses
└── transport/                # HTTP transport (sync + async)

tests/
├── mock/                     # Unit tests (respx HTTP mocking)
├── integration/              # Integration tests (require real server)
├── data/                     # Mock response fixtures
└── helpers.py                # Test utilities

spec/
├── openapi/                  # Canonical OpenAPI spec (editable)
└── vendor/                   # Upstream artifacts (read-only)
```

## Architecture

### Two Client Classes

| Client              | Auth                  | Endpoints                                                  |
| ------------------- | --------------------- | ---------------------------------------------------------- |
| `EbarimtApiClient`  | OAuth2 password grant | District codes, TIN info, merchant info, product tax codes |
| `EbarimtRestClient` | None (local)          | Receipt, info, send_data, bank accounts                    |

Both support context managers (`with` / `async with`) and every method has a sync and `async` variant (e.g., `method()` / `amethod()`).

### Error Hierarchy

```bash
PosApiError
├── PosApiTransportError    — network/timeout/DNS/TLS
├── PosApiDecodeError       — invalid JSON
├── PosApiHttpError         — non-2xx responses
├── PosApiBusinessError     — 2xx but domain-level error
└── PosApiValidationError   — pydantic validation failure
```

### Resource Pattern

Every resource extends `BaseResource`:

```python
class SomeResource(BaseResource):
    @property
    def _path(self) -> str:
        return "/api/endpoint"

    def method(self, payload: Model, *, headers=None) -> Response:
        ...

    async def amethod(self, payload: Model, *, headers=None) -> Response:
        ...
```

### Model Pattern

All models extend `BaseEbarimtModel`:

- Fields use snake_case in Python, camelCase in JSON (via alias generator)
- `extra="ignore"` — unknown server fields are tolerated (server payloads can include extra fields the SDK does not model; we surface what we know about)
- `field_validator` / `field_serializer` for custom logic
- No business rule validation — only structural/format checks

## Validation Philosophy

**Do validate:**

- Regex for stable identifiers (TIN, branch codes)
- Enums for fixed-value fields
- Basic numeric constraints (`>= 0`)

**Do NOT validate:**

- Business rules (dates, conditions, legal logic)
- Cross-field dependencies
- Reference-table lookups (e.g., "is this TIN registered?")

This boundary is intentional. The server owns business rules; the SDK owns shape correctness.

## Testing

- **Mock tests** (`tests/mock/`): Unit tests using `respx` to mock HTTP. Fast, isolated, no external services. Cover both sync and async paths.
- **Integration tests** (`tests/integration/`): Marked `@pytest.mark.integration`. Require live credentials in `.env`. Excluded from CI by default.
- **Fixtures** (`tests/data/`): Mock response templates per endpoint.

To run only unit tests (standard):

```bash
uv run pytest -m "not integration"
```

## Code Style

- Line length: 100 characters (enforced by ruff)
- Target: Python 3.10 syntax
- Imports sorted by isort rules (ruff `I`)
- Strict mypy — all functions must be typed; `disallow_untyped_defs = true`

## OpenAPI Spec

The canonical API contract lives at `spec/openapi/posapi-3.0.yaml`. The `spec/vendor/` directory contains upstream artifacts and should not be edited manually. CI validates spec changes for breaking differences using `oasdiff`.
