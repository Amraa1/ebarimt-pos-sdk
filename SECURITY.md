# Security Policy

## Supported versions

Only the latest release on PyPI receives security fixes. Please upgrade before
reporting an issue:

```bash
pip install --upgrade ebarimt-pos-sdk
```

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Use GitHub's private vulnerability reporting for this repository
(**Security → Report a vulnerability**). Include the SDK version, a minimal
reproduction, and the impact you believe it has. You will get an
acknowledgement within 5 business days.

## What the SDK does to protect you

- **No secrets in logs or errors.** `Authorization`, `Cookie`, API-key headers,
  token-bearing query parameters and `user:pass@` URL userinfo are redacted
  in every log line and in `str(PosApiError)`. Request and response bodies are
  never logged.
- **No secrets in `repr()`.** `ApiClientSettings.password` /
  `client_secret` and all `OAuth2Token` token fields are excluded from the
  dataclass `repr`, so dumping a settings or token object cannot leak them.
- **TLS verification is on by default.** Setting `verify_tls=False` against an
  `https://` endpoint emits a `WARNING` log line; it is intended for local
  development only.
- **Dependency floors track advisories.** Minimum versions in `pyproject.toml`
  are raised when a direct or security-critical transitive dependency
  (e.g. `authlib`, `certifi`) publishes a fix, and CI runs `pip-audit` against
  the locked dependency set weekly and on every lockfile change.

## Operational guidance

- Keep credentials in environment variables or a secrets manager; never
  hard-code them. The SDK does not read `.env` files itself.
- Treat the local POS REST endpoint (`EbarimtRestClient`) as trusted-network
  only — it has no authentication of its own.
- Retries are enabled by default for 5xx and network errors, but only for
  idempotent methods (`GET`/`HEAD`/`OPTIONS`/`PUT`/`DELETE`). Receipt creation
  (`POST /rest/receipt`) is sent exactly once, because PosAPI exposes no
  idempotency key and a retry after a lost response can issue a duplicate
  receipt. Opt `POST` in via `RetrySettings.retry_methods` only if your
  application can detect duplicates.
