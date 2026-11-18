# ebarimt-pos-sdk

[Монгол](https://ebarimt-pos-sdk.readthedocs.io/mn/latest/) · [English](https://ebarimt-pos-sdk.readthedocs.io/en/latest/)

A typed, async-first Python SDK for the **Ebarimt POS API 3.0**, Mongolia's electronic receipt (e-barimt) system.

The SDK gives you two clients:

| Client | Talks to | Use it for |
| --- | --- | --- |
| `EbarimtRestClient` | The PosAPI service running on your own machine or network | Issuing and cancelling receipts, reading PosAPI status, pushing receipts to the tax authority, listing bank accounts |
| `EbarimtApiClient` | The public Ebarimt API (`api.ebarimt.mn`) | Looking up taxpayers, district codes, product tax codes and the BUNA classification |

Every operation has a synchronous method and an `async` twin with an `a` prefix, for example `receipt.create()` and `receipt.acreate()`.

```python
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

with EbarimtRestClient(RestClientSettings(base_url="http://localhost:7080")) as client:
    info = client.info.read()
    print(info.pos_no, info.left_lotteries)
```

## Where to start

- New to the SDK: read [](installation.md), then [](quickstart.md).
- Issuing receipts: [](guides/rest-client.md) and [](guides/errors.md). Read the section on duplicate receipts before going to production.
- Looking up reference data: [](guides/api-client.md).
- Exact signatures and fields: the [API reference](api/index.md).

The official PosAPI 3.0 specification is published by the tax authority's IT centre at [developer.itc.gov.mn](https://developer.itc.gov.mn/docs/ebarimt-api/inbishdm2zj3x-pos-api-3-0-sistemijn-api-holbolt-zaavruud). This documentation covers the SDK, not the business rules of the e-barimt system.

```{toctree}
:maxdepth: 2
:caption: Getting started

installation
quickstart
```

```{toctree}
:maxdepth: 2
:caption: Guides

guides/rest-client
guides/api-client
guides/models
guides/errors
guides/configuration
guides/logging
```

```{toctree}
:maxdepth: 2
:caption: Reference

api/index
Changelog <changelog>
```
