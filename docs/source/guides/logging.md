# Logging

The SDK logs through the standard `logging` module under the logger name `ebarimt_pos_sdk`. It emits nothing until your application configures logging, and it never installs handlers or changes levels itself.

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("ebarimt_pos_sdk").setLevel(logging.DEBUG)
```

## What is logged

| Level | Event | Example |
| --- | --- | --- |
| `DEBUG` | A request is sent | `→ POST http://localhost:7080/rest/receipt [a1b2c3d4]` |
| `DEBUG` | A response arrives | `← 200 in 42ms [a1b2c3d4]` |
| `WARNING` | An attempt failed and will be retried | `retry 1/3 after 503, sleeping 0.73s [a1b2c3d4]` |
| `WARNING` | TLS verification is disabled for an `https://` URL | |

Failures are not logged. They are raised as exceptions, and logging them is up to you.

## Correlating logs and errors

The value in square brackets is a request id. It is the same for all attempts of one call, and it is available on the exception as `error.request_id`.

```python
import logging

from ebarimt_pos_sdk import PosApiError

log = logging.getLogger("pos")

try:
    client.receipt.create(payload)
except PosApiError as error:
    log.error("receipt failed [%s]: %s", error.request_id, error.message)
    raise
```

## Structured fields

Each record carries extra attributes for JSON log pipelines: `request_id`, `http_method`, `http_status`, `duration_ms` and `attempt`. Not every record has all of them.

## What is never logged

Log records contain metadata only: method, URL, status, timing and ids. Request and response bodies and headers are never logged, so receipt contents and credentials stay out of your logs. Token parameters in URLs are masked.

## httpx logs

`httpx` and `httpcore` have their own loggers, which you configure separately. Note that `httpx` logs the full URL at `INFO` level without masking.

```python
import logging.config

logging.config.dictConfig(
    {
        "version": 1,
        "handlers": {"default": {"class": "logging.StreamHandler"}},
        "loggers": {
            "ebarimt_pos_sdk": {"handlers": ["default"], "level": "DEBUG"},
            "httpx": {"handlers": ["default"], "level": "WARNING"},
        },
    }
)
```
