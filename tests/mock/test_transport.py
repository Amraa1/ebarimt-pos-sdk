from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import pytest
import respx

from ebarimt_pos_sdk.errors import PosApiTransportError
from ebarimt_pos_sdk.settings.retry_settings import RetrySettings
from ebarimt_pos_sdk.transport.async_transport import AsyncTransport
from ebarimt_pos_sdk.transport.sync_transport import SyncTransport

BASE = "https://example.com"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    async def _fast_async_sleep(_s: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_async_sleep)


# --------------------------
# Sync retry tests
# --------------------------


@respx.mock
def test_sync_retries_on_5xx_then_succeeds() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_sync_retries_exhaust_returns_last_5xx() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(502))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 502
    assert route.call_count == 3


@respx.mock
def test_sync_retries_on_timeout_then_succeeds() -> None:
    responses: list[Any] = [
        httpx.TimeoutException("timeout"),
        httpx.Response(200, json={"ok": True}),
    ]
    route = respx.get(f"{BASE}/x").mock(side_effect=responses)
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_sync_does_not_retry_on_non_retryable_status() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(400))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 400
    assert route.call_count == 1


@respx.mock
def test_sync_max_retries_one_means_no_retry() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(500))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=1))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 500
    assert route.call_count == 1


@respx.mock
def test_sync_post_body_is_resent_on_retry() -> None:
    """Regression test for opus.md #1 — POST body must be present on each retry."""
    route = respx.post(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("POST", "/x", payload={"hello": "world"})
    assert result.response.status_code == 200
    assert route.call_count == 3
    for call in route.calls:
        assert call.request.content == b'{"hello":"world"}'


@respx.mock
def test_sync_network_error_exhaust_raises() -> None:
    respx.get(f"{BASE}/x").mock(side_effect=httpx.ConnectError("boom"))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=2))
    with pytest.raises(PosApiTransportError):
        transport.send("GET", "/x")


# --------------------------
# Async retry tests
# --------------------------


@pytest.mark.asyncio
@respx.mock
async def test_async_retries_on_5xx_then_succeeds() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = await transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_async_post_body_is_resent_on_retry() -> None:
    route = respx.post(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(504),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = await transport.send("POST", "/x", payload={"a": 1})
    assert result.response.status_code == 200
    assert route.call_count == 2
    for call in route.calls:
        assert call.request.content == b'{"a":1}'


@pytest.mark.asyncio
@respx.mock
async def test_async_does_not_retry_on_non_retryable_status() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(404))
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = await transport.send("GET", "/x")
    assert result.response.status_code == 404
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_network_error_exhaust_raises() -> None:
    respx.get(f"{BASE}/x").mock(side_effect=httpx.ConnectError("boom"))
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=2))
    with pytest.raises(PosApiTransportError):
        await transport.send("GET", "/x")


# --------------------------
# RetrySettings validation
# --------------------------


def test_retry_settings_rejects_invalid_max_retries() -> None:
    with pytest.raises(ValueError, match="max_retries"):
        RetrySettings(max_retries=0)


def test_retry_settings_rejects_negative_backoff() -> None:
    with pytest.raises(ValueError, match="backoff_base_seconds"):
        RetrySettings(backoff_base_seconds=-1)


def test_retry_settings_sleep_seconds_is_exponential() -> None:
    s = RetrySettings(backoff_base_seconds=1.0)
    assert s.sleep_seconds(0) == 1.0
    assert s.sleep_seconds(1) == 2.0
    assert s.sleep_seconds(2) == 4.0


# --------------------------
# Async parity (gaps from sync set)
# --------------------------


@pytest.mark.asyncio
@respx.mock
async def test_async_retries_exhaust_returns_last_5xx() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(502))
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = await transport.send("GET", "/x")
    assert result.response.status_code == 502
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_async_retries_on_timeout_then_succeeds() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.TimeoutException("timeout"),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = await transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_async_max_retries_one_means_no_retry() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(500))
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=1))
    result = await transport.send("GET", "/x")
    assert result.response.status_code == 500
    assert route.call_count == 1


# --------------------------
# Each retryable status individually
# --------------------------


@pytest.mark.parametrize("status", [500, 502, 503, 504])
@respx.mock
def test_sync_retries_each_default_retryable_status(status: int) -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(status), httpx.Response(200, json={})]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 2


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
@respx.mock
def test_sync_does_not_retry_default_non_retryable_statuses(status: int) -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(status))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == status
    assert route.call_count == 1


# --------------------------
# Custom retryable_statuses
# --------------------------


@respx.mock
def test_sync_custom_retryable_statuses_includes_429() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(429), httpx.Response(200, json={})]
    )
    transport = SyncTransport(
        httpx.Client(base_url=BASE),
        retry=RetrySettings(max_retries=3, retryable_statuses=frozenset({429, 503})),
    )
    result = transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_sync_custom_retryable_statuses_excludes_500() -> None:
    """When 500 is removed from retryable set, it should NOT be retried."""
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(500))
    transport = SyncTransport(
        httpx.Client(base_url=BASE),
        retry=RetrySettings(max_retries=3, retryable_statuses=frozenset({429})),
    )
    result = transport.send("GET", "/x")
    assert result.response.status_code == 500
    assert route.call_count == 1


# --------------------------
# Backoff timing
# --------------------------


@respx.mock
def test_sync_backoff_uses_settings_sleep_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    """The transport should sleep `sleep_seconds(attempt)` between attempts."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))

    respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200, json={})]
    )
    transport = SyncTransport(
        httpx.Client(base_url=BASE),
        retry=RetrySettings(max_retries=3, backoff_base_seconds=0.5),
    )
    result = transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert sleeps == [0.5, 1.0]  # 0.5 * 2^0, 0.5 * 2^1


@respx.mock
def test_sync_no_sleep_when_no_retry_needed(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))

    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(200, json={}))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    transport.send("GET", "/x")
    assert sleeps == []


@respx.mock
def test_sync_no_sleep_after_final_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    """With max_retries=N and N consecutive 5xx, sleep happens N-1 times (not after the last)."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))

    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(500))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    transport.send("GET", "/x")
    assert len(sleeps) == 2  # one before retry 2, one before retry 3 — none after attempt 3


@pytest.mark.asyncio
@respx.mock
async def test_async_backoff_uses_settings_sleep_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(s: float) -> None:
        sleeps.append(s)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={})]
    )
    transport = AsyncTransport(
        httpx.AsyncClient(base_url=BASE),
        retry=RetrySettings(max_retries=3, backoff_base_seconds=2.0),
    )
    await transport.send("GET", "/x")
    assert sleeps == [2.0]  # one retry, slept once with attempt=0 → 2.0 * 2^0


# --------------------------
# Mixed failure modes
# --------------------------


@respx.mock
def test_sync_mixed_5xx_then_timeout_then_success() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(503),
            httpx.TimeoutException("slow"),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_async_mixed_network_error_then_5xx_then_success() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.ConnectError("dns"),
            httpx.Response(502),
            httpx.Response(200, json={}),
        ]
    )
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = await transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 3


# --------------------------
# Headers, query params, methods preserved on retry
# --------------------------


@respx.mock
def test_sync_headers_preserved_across_retries() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={})]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    transport.send("GET", "/x", headers={"X-Trace-Id": "abc-123"})
    assert route.call_count == 2
    for call in route.calls:
        assert call.request.headers["x-trace-id"] == "abc-123"


@respx.mock
def test_sync_query_params_preserved_across_retries() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={})]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    transport.send("GET", "/x", params={"tin": "12345"})
    assert route.call_count == 2
    for call in route.calls:
        assert call.request.url.params["tin"] == "12345"


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
@respx.mock
def test_sync_method_preserved_on_retry(method: str) -> None:
    route = respx.route(method=method, url=f"{BASE}/x").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={})]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    payload = {"k": "v"} if method in {"POST", "PUT", "PATCH"} else None
    transport.send(method, "/x", payload=payload)  # type: ignore[arg-type]
    assert route.call_count == 2
    for call in route.calls:
        assert call.request.method == method


# --------------------------
# Non-retryable HTTPError surfaces immediately
# --------------------------


@respx.mock
def test_sync_non_retryable_http_error_does_not_retry() -> None:
    """httpx.HTTPError that is NOT TimeoutException/NetworkError must raise without retrying."""
    calls: list[Any] = []

    def boom(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.RemoteProtocolError("protocol broke")

    respx.get(f"{BASE}/x").mock(side_effect=boom)
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    with pytest.raises(PosApiTransportError):
        transport.send("GET", "/x")
    assert len(calls) == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_non_retryable_http_error_does_not_retry() -> None:
    calls: list[Any] = []

    def boom(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.RemoteProtocolError("protocol broke")

    respx.get(f"{BASE}/x").mock(side_effect=boom)
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    with pytest.raises(PosApiTransportError):
        await transport.send("GET", "/x")
    assert len(calls) == 1
