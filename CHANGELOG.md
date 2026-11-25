# Changelog

All notable changes to this project will be documented here.

---

## [Unreleased]

## [0.7.0] — 2026-11-25

Feature release, no breaking changes to the SDK's API. Operators can register merchants under
their POS with `merchant_registration.create()`, the first API-client call that sends credentials.
The public lookups still need none. The documentation is rewritten and published in English and
Mongolian.

**Upgrading:** `authlib` is no longer installed with the SDK. If your own code imports it, add it
to your dependencies. The password-grant token request now sends the client credentials in the
form body (`client_secret_post`) instead of HTTP Basic. No endpoint used the token before this
release, so no existing call changes.

### Added

- `EbarimtApiClient.merchant_registration.create()` / `acreate()` for eBarimt's
  `saveOprMerchants`: an operator submits a request to register merchant TINs under its POS,
  replacing the manual step in the operator portal. Approval is asynchronous; poll
  `EbarimtRestClient.info.read()` until the TIN appears. Request and response models are
  `CreateMerchantRegistrationRequest` and `CreateMerchantRegistrationResponse` (#111)
- `ApiClientSettings.api_key` and `create_api_settings(..., api_key=...)`, sent as `X-API-KEY` by
  `merchant_registration` only and hidden from `repr()` (#111)
- `PosApiConfigurationError` (a `PosApiError`), raised before anything is sent when a call needs
  settings that are missing. Its message lists every missing field and `request_sent` is `False`
  (#111)

### Changed

- `merchant_registration` is the only resource that sends an OAuth2 token. The public lookup
  endpoints still send no `Authorization` header, even when credentials are configured (#111)
- The password-grant token request is now sent through the client's own `httpx` clients, so it
  honours the client's `proxy`, `verify_tls`, `timeout_s` and any injected client. Client
  credentials are sent in the form body (`client_secret_post`). A token response without
  `expires_in` is assumed to last 300 seconds instead of being treated as already expired, and a
  missing `token_url` raises `PosApiConfigurationError` (#111)
- `authlib` is no longer a dependency (#111)
- `PosApiHttpError` keeps the server's explanation from a `msg` field when the body has no
  `message` field (#111)

### Fixed

- The password-grant token request ignored the client's proxy, TLS and timeout settings and any
  injected client: Authlib's `OAuth2Client` silently dropped the `client=` argument and sent the
  request through its own default `httpx` client. Behind a required proxy, the token request
  would have failed (#111)

### Documentation

- Rewrote the Read the Docs site: installation, quickstart, guides for both clients, models and
  validation, error handling, configuration and logging, plus an API reference generated from the
  current modules (the previous reference pointed at modules that no longer exist)
- The documentation is now published in English and Mongolian from one set of sources; Mongolian
  lives in `docs/locale/mn` as gettext catalogues (see `docs/README.md`)
- README: default headers are passed to the client constructor, not to the settings object
- README: the public API client example no longer passes `client_id`, `username` and `password`,
  and the feature list and client table no longer claim OAuth2 for it. The public endpoints need no
  credentials, and the client never sent a token, so the example implied an authentication that
  did not happen. The settings, factory and client docstrings say the same (#112)

## [0.6.0] — 2026-11-18

Feature release, no breaking changes. A failed request now tells you whether it could have reached
PosAPI, so a failed `receipt.create` can be safely resent when it never left the client. You can
let the SDK do that resend for you by opting in.

### Added

- `PosApiTransportError.request_sent` tells whether the failed request could have reached the
  server. It is `False` for connect-phase failures (`httpx.ConnectError`, `httpx.ConnectTimeout`,
  `httpx.ProxyError`) and when the OAuth token fetch fails before the resource request, so a
  failed `receipt.create` can be resent safely; it is `True` for everything else (read/write
  timeouts, dropped connections, unknown errors). With retries, it reflects the final attempt.
  Shown as `RequestSent:` in the error's string form (#106)
- `RetrySettings.retry_unsent` (default `False`). When on, `POST`/`PATCH` (any method outside
  `retry_methods`) may be re-sent up to `max_retries` times, but only after a failure that proves
  the request never left the client (`PosApiTransportError.request_sent` is `False`). Responses,
  including 5xx, and failures after the request may have been sent still end on the first
  attempt, so it cannot duplicate a receipt. New `RetrySettings.may_retry(method, *,
  request_sent)` encodes the rule; `attempts_for` returns `max_retries` for every method when the
  flag is on (#108)

### Fixed

- `PosApiTransportError.cause` now holds the underlying `httpx` (or authlib) exception instead of
  always being `None` (#106)
- `httpx.ProxyError` (the proxy refused or failed the tunnel) is now retried for idempotent
  methods, like other connect failures. It was previously raised on the first attempt. `POST`
  and `PATCH` are still sent once by default (#107)

## [0.5.0] — 2026-11-01

Behaviour release: closes every issue open since June (#77–#82). Two public defaults change —
read **Changed** before upgrading.

### Changed

- **Transport no longer retries non-idempotent requests.** `receipt.create` (`POST`) could be
  re-sent after a timeout even though PosAPI may already have persisted the receipt, issuing a
  duplicate е-баримт. Retries now apply only to methods listed in the new
  `RetrySettings.retry_methods` (default: `GET`/`HEAD`/`OPTIONS`/`PUT`/`DELETE`); `POST` and
  `PATCH` are sent exactly once regardless of `max_retries`. A `POST` that previously succeeded
  on a later attempt after a transient 5xx now surfaces that first failure as
  `PosApiHttpError` / `PosApiTransportError`. Opt in with
  `RetrySettings(retry_methods=RetrySettings.DEFAULT_RETRY_METHODS | {"POST"})`. PosAPI 3.0
  exposes no idempotency key, so none is threaded through (#77)
- **Retry backoff is now jittered, capped, and honours `Retry-After`.** `RetrySettings.sleep_seconds`
  applies *full jitter* (uniform in `[0, backoff]`) so devices that fail together do not retry in
  lockstep, and caps the delay at the new `max_backoff_seconds` (default 30s). When the server sends
  a `Retry-After` header (delta-seconds or HTTP-date, RFC 9110 §10.2.3) the transports sleep for
  that long instead (not jittered, still capped). `429 Too Many Requests` is now in the default
  `retryable_statuses`, so idempotent requests throttled with 429 are retried instead of failing
  immediately. Set `jitter=False` for deterministic timing in tests (#80)

### Added

- `PasswordGrantAuth` now handles a `401 Unauthorized` transparently: when the server rejects a
  token the client still considered valid (revocation, clock drift, server-side session purge),
  the auth flow renews the token once — refresh grant if available, falling back to a full
  password grant if the refresh is rejected too — re-sets `Authorization`, and re-sends the
  request exactly once. A second `401` is returned to the caller unchanged, so a genuinely
  invalid credential cannot loop. Works for both `auth_flow` and `async_auth_flow`; a token
  already renewed by a concurrent caller is reused instead of fetched again (#81)
- `RetrySettings.retry_methods`, `RetrySettings.DEFAULT_RETRY_METHODS`,
  `RetrySettings.is_retryable_method()` and `RetrySettings.attempts_for()` (#77)
- `RetrySettings.max_backoff_seconds`, `RetrySettings.jitter`, `RetrySettings.respect_retry_after`;
  `sleep_seconds()` takes an optional `retry_after` keyword (#80)
- `ebarimt_pos_sdk.transport.parse_retry_after()` — public parser for `Retry-After` values (#80)

### Fixed

- `PosApiBusinessError` is now actually raised: a 2xx response whose JSON body carries
  `status: "ERROR"` (PosAPI's domain-level rejection, e.g. an invalid receipt) raises
  `PosApiBusinessError` with the server's `status`/`message`/`code` and the request/response
  attached. Previously such bodies surfaced as a confusing `PosApiValidationError` because they
  lack the fields of the success model (#78)
- Response validation failures no longer escape as bare `pydantic.ValidationError`: every 2xx body
  now goes through `BaseResource._validate_response`, so a malformed server payload raises
  `PosApiValidationError(stage="response")` with `request`/`response` attached. `InfoResource`
  and `BankAccountsResource` were bypassing the wrapper; `BankAccountsResource` additionally
  rejects a non-array body with a response-stage validation error instead of a `TypeError` (#79)
- A malformed `date` in a non-2xx error body no longer raises `ValueError` inside the error
  handler and masks the real `PosApiHttpError`; `date` is left `None` instead (#82)
- Release workflow: publishing to PyPI is now gated on a `verify` job (ruff, ty, unit tests)
  that must pass on the tagged commit (#82)

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
- CI hardening: every GitHub Action is pinned to a full commit SHA (with the resolved version in a
  trailing comment) instead of a mutable major tag; `persist-credentials: false` on all checkouts; release build now uses Python 3.12
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
