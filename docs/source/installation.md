# Installation

The SDK requires Python 3.10 or newer.

```bash
pip install ebarimt-pos-sdk
```

With `uv`:

```bash
uv add ebarimt-pos-sdk
```

The package installs `httpx` and `pydantic` (v2) as dependencies.

## Optional: SOCKS proxy support

`EbarimtApiClient` can send its requests through a proxy. HTTP proxies work out of the box. For a SOCKS proxy, install the `httpx` extra as well:

```bash
pip install "httpx[socks]"
```

## What you need before you start

To issue receipts you need a running **PosAPI 3.0** service. It is the program distributed by the tax authority that signs receipts and forwards them to the central system. The SDK does not include it. PosAPI listens on port `7080` by default, so the base URL is usually `http://localhost:7080`.

The lookup endpoints used by `EbarimtApiClient` are public and need no PosAPI installation. They may only be reachable from inside Mongolia, see [](guides/api-client.md#using-a-proxy).

## Check the installation

```python
from importlib.metadata import version

print(version("ebarimt-pos-sdk"))
```
