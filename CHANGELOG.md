# Changelog

All notable changes to this project will be documented here.

---

## [Unreleased]

## [0.4.2] — 2026-11-01

### Security

- Raised dependency floors: `authlib>=1.9.1` (fixes JWS signature-verification bypass,
  `is_secure_transport()` loopback spoofing via URL userinfo, empty-HMAC-key acceptance and
  related 2026 advisories) and a new explicit `certifi>=2026.10.18` floor (drops the compromised
  "emSign ECC Root CA - G3" root from the trust store used for every HTTPS call)
- Refreshed `uv.lock`: `cryptography` 46.0.7 → 50.0.2 (statically linked OpenSSL advisory, name-
  constraint wildcard escape, chain-resolution DoS), `joserfc` 1.6.4 → 1.7.7, `idna` → 3.20,
  `anyio` → 4.16.0, `urllib3` → 2.8.0. `pip-audit` reports no known vulnerabilities against the lock
- Credentials no longer appear in `repr()`: `ApiClientSettings.password` / `client_secret` and
  `OAuth2Token.access_token` / `refresh_token` / `raw` are `repr=False`, so a settings or token
  object that lands in a log line, traceback or debugger dump cannot leak secrets
- `redact_url()` now also masks `user:pass@` URL userinfo (e.g. a proxy or base URL carrying
  basic-auth credentials) in log lines and `PosApiError` messages
- `PosApiHttpError` fallback message (non-JSON error bodies) now embeds the *redacted* request
  URL instead of httpx's raw `Request` repr, which printed query parameters verbatim
- `verify_tls=False` against an `https://` base URL now emits a `WARNING` log line instead of
  silently disabling certificate verification
- New `Dependency Audit` workflow runs `pip-audit --strict` against the locked dependency set on
  every `pyproject.toml` / `uv.lock` change and weekly on a schedule
- CI hardening: `persist-credentials: false` on all checkouts; release build now uses Python 3.12
  (was 3.9, below the package's own `requires-python`); dev-tools job pinned to the same uv
  version as the release job
- Added `SECURITY.md` with the disclosure process and the SDK's secret-handling guarantees

### Fixed

- `BaseResource` payload parameters are typed `BaseModel | dict[str, Any]` instead of
  `T | dict[str, Any]`, resolving a `ty` 0.0.95 generic-bound diagnostic on
  `ReceiptResource.delete` / `adelete` (no runtime change)

## [0.4.0] — 2026-06-09

### Security

- Redact `Authorization` header in `PosApiError.__str__()` to prevent token exposure in logs
- Hoisted URL/header redaction into a shared `_redaction` module reused by error formatting and the new logging; fixed a leak where `build_transport_error` embedded the raw (unredacted) request URL in the error message (#86)

### Added

- `proxy` argument on `EbarimtApiClient` (`str | httpx.Proxy`) to route the public API through an HTTP/SOCKS proxy — e.g. reaching the Mongolia-only API from another region. Forwarded to the underlying httpx clients; combining it with an injected `sync_client`/`async_client` raises `ValueError`; SOCKS needs the `httpx[socks]` extra (#91)
- Token refresh flow in `PasswordGrantAuth` — tries refresh token before falling back to full password grant
- `_refresh_token_sync()` and `_refresh_token_async()` methods on `PasswordGrantAuth`
- Retry logic in `SyncTransport` and `AsyncTransport` — up to 3 attempts with backoff on 5xx / network errors
- Structured request/response logging in the transport layer under the `ebarimt_pos_sdk.*` namespace: lifecycle lines at `DEBUG`, retries at `WARNING`, a per-request `request_id` (carried via `request.extensions` and exposed on `PosApiError.request_id`), and structured `extra` fields. Metadata only — headers/bodies are never logged and sensitive URL query params are redacted. A `NullHandler` is attached to the package root so nothing is emitted until the application configures logging (#86)
- `__post_init__` validation on `ApiClientSettings` — rejects empty/whitespace `token_url`, `client_id`, `username`, `password` when supplied (fields themselves are optional; see [Changed])
- `@field_validator` on `Item.qty` and `Item.unit_price` — rejects values `<= 0`
- `@field_validator` on `SubReceipt.items` — rejects empty list
- UTC timezone attached to parsed `date` field in `CreateReceiptResponse`
- Async test variants for `district_code`, `tin_info`, `merchant_info`, and `product_tax_code` resources
- Alias round-trip tests in `tests/mock/test_base_model_aliases.py`
- `BunaResource` (exposed as `EbarimtApiClient.buna`) wrapping `GET /api/info/check/barcode/v2[/{code}...]` — hierarchical БҮНА (Бараа, Үйлчилгээний Нэгдсэн Ангилал) classification drill-down. Variable depth (0..6 segments) in logical top-down order; `client.buna.read()` returns the top-level Салбар list, `client.buna.read("0", "01", ...)` drills down one level per segment. Returns `GetBunaResponse` (a `RootModel[list[list[str]]]`); structural validation only per the SDK's "validate structure, not policy" rule
- Optional `path: str | None` argument on `BaseResource._send_sync_request` and `_send_async_request` for resources that build dynamic URLs (used by `BunaResource`)
- `tests/data/buna.py` fixtures and `tests/mock/test_buna.py` covering top-level, drill-down, leaf-barcode, sync + async, and blank-segment rejection paths

### Changed

- Tooling: replaced mypy with `ty` (Astral) as the static type checker, and moved ruff config from `pyproject.toml` to `ruff.toml` (#87, #90)
- **Breaking**: `EbarimtApiClient` no longer attaches `PasswordGrantAuth` to its `httpx` clients. The public ebarimt info endpoints (`/api/info/check/getBranchInfo`, `getTinInfo`, `getInfo`, `barcode/v2/...`, and `/api/receipt/receipt/getProductTaxCode`) have no `security:` declaration in the OpenAPI spec — the OAuth2 token fetch was an unnecessary round-trip. The `auth/` module (`PasswordGrantAuth`, `OAuth2Token`) is kept intact for any future endpoint that may require token auth
- **Breaking**: `ApiClientSettings` credential fields (`token_url`, `client_id`, `username`, `password`) are now optional `str | None = None`. `factory.create_api_settings` likewise accepts `client_id`, `username`, `password` as optional keyword arguments. Existing call sites that pass these continue to work; new call sites for the public info endpoints can construct settings as `ApiClientSettings(base_url=...)`
- `DistrictCodeResource`, `BranchInfo`, and `GetDistrictCodeResponse` moved from `resources/api/info/` to a dedicated `resources/api/district/` package and re-exported from `ebarimt_pos_sdk.resources`
- Mock tests for `district_code`, `tin_info`, `merchant_info`, `product_tax_code` no longer mock token endpoints or assert `token_route.called`; `_settings()` helpers construct credential-free `ApiClientSettings(base_url=BASE_API_URL)`

### Fixed

- `TaxType` raw-string Literal corrected from `NOT_VAT` to `NO_VAT` to match the value the live server accepts; the `TaxType` enum was already correct (#88)
- Token fetch / refresh errors now raise `PosApiTransportError` instead of raw authlib / httpx exceptions
- Async token lock race condition: removed unprotected pre-lock read, all logic now inside `async with self._async_lock`
- Sync token lock simplified to same pattern for consistency
- `ReceiptResource.create` / `acreate` refactored to use `_send_sync_request` / `_send_async_request` helpers (consistent with `delete`)
- `except Exception` in `BaseResource._decode_json` narrowed to `except ValueError`
- Removed stray `print(TOKEN_URL)` in `tests/helpers.py`
- `resources/__init__.py` import paths repaired — the district-package move had left `from .api.info.info import DistrictCodeResource` in place, leaving the SDK unimportable

---

## [0.3.2] — 2026-05-29

### Fixed

- `MerchantInfo.is_government` is now nullable (`bool | None`). The `getInfo`
  endpoint can return `isGovernment: null`, which previously raised a pydantic
  `bool_type` validation error (#74)

## [0.2.8] — 2025

- Bug fix (#65)

## [0.2.7]

- Bug fix (#64)
- Patch (#63)

## [0.2.5]

- Fix (#61)

## [0.2.4]

- Fixing error responses (#58, #57)
- Fix `CreateReceiptResponse` date field validation (#56)

## [0.2.3]

- Minor patches (#55)

## [0.2.2]

- Patched create ebarimt response (#54)

## [0.2.1]

- Added Codecov config (#53)
- Fixing bugs (#50)

## [0.2.0]

- Fixing test cases (#49)
- Improve code coverage (#48)
- Add typing and mypy checks (#46)
- Abstract `model_dump` (#45)

## [0.1.4]

- Fixes (#43, #44)

## [0.1.3]

- Release v0.1.3 (#42)

## [0.1.2]

- Better error responses (#40)

## [0.1.1]

- Better error response (#38)
- Docs improvements (#33–#37)

## [0.1.0]

- Initial stable release (#32)

## [0.1.0b2]

- Beta release 2 (#29)

## [0.1.0b]

- Beta release (#28)
