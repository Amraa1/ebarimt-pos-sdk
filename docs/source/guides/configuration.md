# Configuration

Clients are configured with a settings object passed to the constructor. Settings are immutable dataclasses: build them once and share them.

```python
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

settings = RestClientSettings(
    base_url="http://localhost:7080",
    timeout_s=5.0,
)
client = EbarimtRestClient(settings)
```

## Common settings

`RestClientSettings` and `ApiClientSettings` share these fields.

| Field | Default | Meaning |
| --- | --- | --- |
| `base_url` | required | Root URL of the service. A trailing slash is ignored. |
| `timeout_s` | `10.0` | Timeout in seconds, applied to connecting, sending and reading. |
| `verify_tls` | `True` | Verify the server's TLS certificate. |
| `retry` | `RetrySettings()` | Retry policy, described below. |

`ApiClientSettings` adds optional credential fields, see [](api-client.md#authentication).

Setting `verify_tls=False` on an `https://` URL logs a warning, because it exposes the traffic to interception. Do not use it in production.

## Retries

The SDK retries a request when it fails with a network error or when the server answers with one of the retryable status codes. Between attempts it waits with exponential backoff.

```python
from ebarimt_pos_sdk import RestClientSettings
from ebarimt_pos_sdk.settings import RetrySettings

settings = RestClientSettings(
    base_url="http://localhost:7080",
    retry=RetrySettings(max_retries=5, max_backoff_seconds=10.0),
)
```

| Field | Default | Meaning |
| --- | --- | --- |
| `max_retries` | `3` | Total number of attempts, including the first one. Must be at least 1. |
| `retryable_statuses` | `429, 500, 502, 503, 504` | Status codes that trigger a retry. |
| `backoff_base_seconds` | `1.0` | The wait before retry *n* is at most `base * 2**n`. |
| `max_backoff_seconds` | `30.0` | Upper limit for a single wait. |
| `jitter` | `True` | Wait a random time between zero and the computed backoff. |
| `respect_retry_after` | `True` | Use the server's `Retry-After` header instead of the computed backoff. |
| `retry_methods` | `GET, HEAD, OPTIONS, PUT, DELETE` | HTTP methods that may be retried. |
| `retry_unsent` | `False` | Also retry other methods when the request provably never left the client. |

Jitter keeps a group of POS machines that fail at the same moment from retrying at the same moment. Set `jitter=False` if you need predictable timing in tests.

To switch retries off, set `max_retries=1`.

If every attempt fails, the error from the last attempt is raised.

(retrying-receipt-requests)=
### Retrying receipt requests

Retries apply only to the methods in `retry_methods`. `receipt.create()` is a `POST`, so by default it is sent once, whatever `max_retries` says. This is deliberate: if PosAPI stored the receipt and only the response was lost, a retry would issue a second receipt.

`receipt.delete()`, `info.read()` and all lookups use retryable methods.

You have two ways to change this for `POST`:

```python
# Safe: resend only when the request never left this machine
# (connection refused, DNS failure, connect timeout, proxy refused).
RetrySettings(retry_unsent=True)

# Unsafe unless you can detect duplicates: retry POST like any other method.
RetrySettings(retry_methods=RetrySettings.DEFAULT_RETRY_METHODS | {"POST"})
```

With `retry_unsent=True` a `POST` still ends after the first attempt for any response, including `503`, and for any failure after the request may have been sent.

(default-headers)=
## Default headers

Pass `headers` to the client constructor to send them with every request.

```python
client = EbarimtRestClient(settings, headers={"X-Request-Source": "pos-42"})
```

A `headers` argument on a single method call overrides a default header with the same name.

## Using your own httpx client

Pass your own `httpx.Client` and `httpx.AsyncClient` when you need settings the SDK does not expose, such as connection limits, a custom transport, or event hooks.

```python
import httpx

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

settings = RestClientSettings(base_url="http://localhost:7080")
http = httpx.Client(
    base_url=settings.base_url,
    timeout=httpx.Timeout(10.0, connect=2.0),
    limits=httpx.Limits(max_connections=10),
)

client = EbarimtRestClient(settings, sync_client=http)
```

Two things change when you inject a client:

- The SDK uses your client's `base_url`, timeout and TLS options. `timeout_s` and `verify_tls` from the settings are not applied to it, so set `base_url` on your client yourself.
- The SDK does not close a client it did not create. Closing it is your job.

The retry policy from the settings still applies.
