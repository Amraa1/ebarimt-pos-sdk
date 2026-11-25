# Error handling

Every exception the SDK raises on purpose derives from `PosApiError`. Catch a subclass to react to one kind of failure, or the base class to catch them all.

```text
PosApiError
├── PosApiValidationError
├── PosApiTransportError
├── PosApiHttpError
├── PosApiDecodeError
├── PosApiBusinessError
└── PosApiConfigurationError
```

All of them can be imported from `ebarimt_pos_sdk`.

## Which error means what

| Error | When | Was the request processed? |
| --- | --- | --- |
| `PosApiConfigurationError` | The call needs settings that are missing, such as credentials. Nothing was sent. | No |
| `PosApiValidationError`, `stage == "request"` | Your payload is malformed. Nothing was sent. | No |
| `PosApiTransportError`, `request_sent == False` | The connection could not be opened. | No |
| `PosApiTransportError`, `request_sent == True` | The connection failed after the request may have been sent. | Unknown |
| `PosApiHttpError` | The server returned 4xx or 5xx. | Normally no, but treat 5xx as unknown |
| `PosApiBusinessError` | The server returned 2xx with an error status in the body. | No, it was rejected |
| `PosApiDecodeError` | The server returned 2xx with a body that is not JSON. | Unknown |
| `PosApiValidationError`, `stage == "response"` | The server returned 2xx with JSON the SDK cannot parse. | Probably yes |

## Common attributes

Every error has these attributes:

| Attribute | Content |
| --- | --- |
| `message` | Human-readable description. |
| `request` | The `httpx.Request`, or `None` if no request was built. |
| `response` | The `httpx.Response`, or `None` if none was received. |
| `cause` | The underlying exception, if any. |
| `request_id` | Short id that also appears in the SDK's log lines for this request. |

`str(error)` is safe to log. `Authorization`, `Cookie` and similar headers are masked, and so are token parameters in the URL.

## Validation errors

`PosApiValidationError` wraps a pydantic `ValidationError`.

```python
from ebarimt_pos_sdk import PosApiValidationError

try:
    client.receipt.create({"branch_no": "001"})
except PosApiValidationError as error:
    print(error.stage)  # "request"
    print(error.model)  # "CreateReceiptRequest"
    for item in error.errors:
        print(item["loc"], item["msg"])
```

`stage` is `"request"` when your payload is wrong and `"response"` when the server's answer does not match the model. A response-stage error on `receipt.create()` means PosAPI answered with success, so the receipt very likely exists. The raw body is in `error.response.text`.

## HTTP errors

`PosApiHttpError` is raised for any 4xx or 5xx response. PosAPI usually explains the problem in the body, and the SDK copies that into the error.

```python
from ebarimt_pos_sdk import PosApiHttpError

try:
    client.receipt.create(payload)
except PosApiHttpError as error:
    print(error.response.status_code)  # HTTP status code
    print(error.status)  # "status" field of the error body, if present
    print(error.message)  # includes the server's message
```

## Business errors

PosAPI reports some rejections with HTTP 200 and a body such as `{"status": "ERROR", "message": "..."}`. The SDK turns these into `PosApiBusinessError`. For `merchant_registration`, a numeric `status` other than `200` is a rejection, and the message comes from the body's `msg` field.

```python
from ebarimt_pos_sdk import PosApiBusinessError

try:
    client.receipt.create(payload)
except PosApiBusinessError as error:
    print(error.status, error.code)
    print(error.message)  # the server's explanation, usually in Mongolian
```

The message comes from the server unchanged. It is the text to show to the cashier or to write to your log.

## Transport errors

`PosApiTransportError` means no response arrived. `cause` holds the original `httpx` exception.

Its `request_sent` attribute answers the question that matters for receipts: could the server have received the request?

- `False`: the failure happened before any byte was sent. This covers a refused connection, a DNS failure, a connect timeout and a proxy that refused the tunnel. The server cannot have acted on the request.
- `True`: the request may have arrived. This covers read and write timeouts, a dropped connection and any failure the SDK does not recognise.

(avoiding-duplicate-receipts)=
## Avoiding duplicate receipts

PosAPI 3.0 has no idempotency key. If you send the same receipt twice, two receipts are issued. For that reason the SDK sends `receipt.create()` exactly once and leaves the decision to you.

```python
from ebarimt_pos_sdk import (
    PosApiBusinessError,
    PosApiHttpError,
    PosApiTransportError,
    PosApiValidationError,
)

try:
    receipt = client.receipt.create(payload)
except PosApiValidationError as error:
    if error.stage == "request":
        ...  # fix the payload; nothing was sent
    else:
        ...  # PosAPI answered with success; do not resend, inspect error.response
except PosApiBusinessError as error:
    ...  # rejected by PosAPI; show error.message, fix the data, send again
except PosApiHttpError as error:
    ...  # 4xx: fix the request. 5xx: check before resending
except PosApiTransportError as error:
    if not error.request_sent:
        ...  # never left this machine; safe to send again
    else:
        ...  # outcome unknown; do not resend automatically
```

When the outcome is unknown, do not resend automatically. Record the attempt and find out whether the receipt exists before you issue another one, for example by having an operator check it.

If the only failure you want to ride out is a PosAPI service that is briefly unreachable, let the SDK do the safe resend for you with `RetrySettings(retry_unsent=True)`. See [](configuration.md#retrying-receipt-requests).
