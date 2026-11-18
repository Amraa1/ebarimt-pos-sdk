"""RetrySettings.retry_unsent: re-send POST/PATCH only after never-sent failures."""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest
import respx

from ebarimt_pos_sdk.errors import PosApiTransportError
from ebarimt_pos_sdk.settings.retry_settings import RetrySettings
from ebarimt_pos_sdk.transport.async_transport import AsyncTransport
from ebarimt_pos_sdk.transport.sync_transport import SyncTransport

BASE = "https://example.com"
URL = f"{BASE}/rest/receipt"
OPT_IN = RetrySettings(max_retries=3, retry_unsent=True)

NOT_SENT = [
    httpx.ConnectError("refused"),
    httpx.ConnectTimeout("connect timeout"),
    httpx.ProxyError("tunnel refused"),
]
MAYBE_SENT = [
    httpx.ReadTimeout("read timeout"),
    httpx.WriteTimeout("write timeout"),
    httpx.ReadError("connection reset"),
    httpx.RemoteProtocolError("server disconnected"),
]


def _ids(excs: list[httpx.HTTPError]) -> list[str]:
    return [type(e).__name__ for e in excs]


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    async def _fast_async_sleep(_s: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_async_sleep)


# --------------------------
# RetrySettings
# --------------------------


def test_retry_unsent_off_by_default() -> None:
    r = RetrySettings()
    assert r.retry_unsent is False
    assert r.attempts_for("POST") == 1
    assert not r.may_retry("POST", request_sent=False)


def test_may_retry_matrix() -> None:
    assert OPT_IN.attempts_for("POST") == 3
    assert OPT_IN.may_retry("POST", request_sent=False)
    assert not OPT_IN.may_retry("POST", request_sent=True)
    assert not OPT_IN.may_retry("patch", request_sent=True)
    # Idempotent methods are unaffected by the flag.
    assert OPT_IN.may_retry("GET", request_sent=True)
    assert RetrySettings().may_retry("GET", request_sent=True)


# --------------------------
# Sync
# --------------------------


@pytest.mark.parametrize("exc", NOT_SENT, ids=_ids(NOT_SENT))
@respx.mock
def test_sync_post_retried_after_unsent_failure(exc: httpx.HTTPError) -> None:
    route = respx.post(URL).mock(side_effect=[exc, httpx.Response(200, json={})])
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=OPT_IN)
    result = transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert result.response.status_code == 200
    assert route.call_count == 2


@pytest.mark.parametrize("exc", MAYBE_SENT, ids=_ids(MAYBE_SENT))
@respx.mock
def test_sync_post_not_retried_after_maybe_sent_failure(exc: httpx.HTTPError) -> None:
    route = respx.post(URL).mock(side_effect=[exc, httpx.Response(200, json={})])
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=OPT_IN)
    with pytest.raises(PosApiTransportError) as info:
        transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert route.call_count == 1
    assert info.value.request_sent is True


@respx.mock
def test_sync_post_not_retried_on_5xx_even_with_opt_in() -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(503))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=OPT_IN)
    result = transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert result.response.status_code == 503
    assert route.call_count == 1


@respx.mock
def test_sync_post_unsent_then_maybe_sent_stops() -> None:
    """A retry that then loses its response must not be retried again."""
    route = respx.post(URL).mock(
        side_effect=[
            httpx.ConnectError("refused"),
            httpx.ReadTimeout("read"),
            httpx.Response(200, json={}),
        ]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=OPT_IN)
    with pytest.raises(PosApiTransportError) as info:
        transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert route.call_count == 2
    assert info.value.request_sent is True


@respx.mock
def test_sync_post_unsent_then_5xx_returns_5xx() -> None:
    route = respx.post(URL).mock(
        side_effect=[httpx.ConnectError("refused"), httpx.Response(503), httpx.Response(200)]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=OPT_IN)
    result = transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert result.response.status_code == 503
    assert route.call_count == 2


@respx.mock
def test_sync_post_unsent_exhausts_retries() -> None:
    route = respx.post(URL).mock(side_effect=httpx.ConnectError("refused"))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=OPT_IN)
    with pytest.raises(PosApiTransportError) as info:
        transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert route.call_count == 3
    assert info.value.request_sent is False


@respx.mock
def test_sync_post_unsent_not_retried_without_opt_in() -> None:
    route = respx.post(URL).mock(side_effect=httpx.ConnectError("refused"))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    with pytest.raises(PosApiTransportError):
        transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert route.call_count == 1


@respx.mock
def test_sync_patch_retried_after_unsent_failure() -> None:
    route = respx.patch(URL).mock(
        side_effect=[httpx.ConnectTimeout("connect"), httpx.Response(200, json={})]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=OPT_IN)
    result = transport.send("PATCH", "/rest/receipt", payload={"k": "v"})
    assert result.response.status_code == 200
    assert route.call_count == 2


# --------------------------
# Async
# --------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("exc", NOT_SENT, ids=_ids(NOT_SENT))
@respx.mock
async def test_async_post_retried_after_unsent_failure(exc: httpx.HTTPError) -> None:
    route = respx.post(URL).mock(side_effect=[exc, httpx.Response(200, json={})])
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=OPT_IN)
    result = await transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert result.response.status_code == 200
    assert route.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("exc", MAYBE_SENT, ids=_ids(MAYBE_SENT))
@respx.mock
async def test_async_post_not_retried_after_maybe_sent_failure(exc: httpx.HTTPError) -> None:
    route = respx.post(URL).mock(side_effect=[exc, httpx.Response(200, json={})])
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=OPT_IN)
    with pytest.raises(PosApiTransportError):
        await transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_post_not_retried_on_5xx_even_with_opt_in() -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(503))
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=OPT_IN)
    result = await transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert result.response.status_code == 503
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_post_unsent_then_maybe_sent_stops() -> None:
    route = respx.post(URL).mock(
        side_effect=[httpx.ConnectError("refused"), httpx.ReadTimeout("read")]
    )
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=OPT_IN)
    with pytest.raises(PosApiTransportError) as info:
        await transport.send("POST", "/rest/receipt", payload={"k": "v"})
    assert route.call_count == 2
    assert info.value.request_sent is True
