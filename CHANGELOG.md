# Changelog

All notable changes to this project will be documented here.

---

## [Unreleased]

### Security

- Redact `Authorization` header in `PosApiError.__str__()` to prevent token exposure in logs

### Added

- Token refresh flow in `PasswordGrantAuth` — tries refresh token before falling back to full password grant
- `_refresh_token_sync()` and `_refresh_token_async()` methods on `PasswordGrantAuth`
- Retry logic in `SyncTransport` and `AsyncTransport` — up to 3 attempts with backoff on 5xx / network errors
- Debug logging in transport layer (`logging.getLogger(__name__)`) at `DEBUG` level
- `__post_init__` validation on `ApiClientSettings` — rejects empty `token_url`, `client_id`, `username`, `password` at construction time
- `@field_validator` on `Item.qty` and `Item.unit_price` — rejects values `<= 0`
- `@field_validator` on `SubReceipt.items` — rejects empty list
- UTC timezone attached to parsed `date` field in `CreateReceiptResponse`
- Async test variants for `district_code`, `tin_info`, `merchant_info`, and `product_tax_code` resources
- Alias round-trip tests in `tests/mock/test_base_model_aliases.py`

### Fixed

- Token fetch / refresh errors now raise `PosApiTransportError` instead of raw authlib / httpx exceptions
- Async token lock race condition: removed unprotected pre-lock read, all logic now inside `async with self._async_lock`
- Sync token lock simplified to same pattern for consistency
- `ReceiptResource.create` / `acreate` refactored to use `_send_sync_request` / `_send_async_request` helpers (consistent with `delete`)
- `except Exception` in `BaseResource._decode_json` narrowed to `except ValueError`
- Removed stray `print(TOKEN_URL)` in `tests/helpers.py`

---

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
