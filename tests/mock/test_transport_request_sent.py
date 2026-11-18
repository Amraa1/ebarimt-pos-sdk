"""#106 — transport errors say whether the request could have reached the server."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import pytest
import respx

from ebarimt_pos_sdk.auth.password_grant import PasswordGrantAuth
from ebarimt_pos_sdk.errors import PosApiTransportError
from ebarimt_pos_sdk.settings import ApiClientSettings
from ebarimt_pos_sdk.settings.retry_settings import RetrySettings
from ebarimt_pos_sdk.transport.async_transport import AsyncTransport
from ebarimt_pos_sdk.transport.sync_transport import SyncTransport

BASE = "https://example.com"

NOT_SENT = [
    httpx.ConnectError("refused"),
    httpx.ConnectTimeout("connect timeout"),
    httpx.ProxyError("tunnel refused"),
]
MAYBE_SENT = [
    httpx.ReadTimeout("read timeout"),
    httpx.WriteTimeout("write timeout"),
    httpx.PoolTimeout("pool timeout"),
    httpx.RemoteProtocolError("server disconnected"),
    httpx.ReadError("connection reset"),
    httpx.TimeoutException("generic timeout"),
    httpx.HTTPError("unknown"),
]
ALL = [(e, False) for e in NOT_SENT] + [(e, True) for e in MAYBE_SENT]
IDS = [type(e).__name__ for e, _ in ALL]


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    async def _fast_async_sleep(_s: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_async_sleep)


@pytest.mark.parametrize(("exc", "expected_sent"), ALL, ids=IDS)
@respx.mock
def test_sync_post_reports_request_sent(exc: httpx.HTTPError, expected_sent: bool) -> None:
    respx.post(f"{BASE}/rest/receipt").mock(side_effect=exc)
    transport = SyncTransport(httpx.Client(base_url=BASE))
    with pytest.raises(PosApiTransportError) as info:
        transport.send("POST", "/rest/receipt", payload={"k": "v"})
    err = info.value
    assert err.request_sent is expected_sent
    assert err.cause is exc
    assert err.__cause__ is exc
    assert err.request is not None
    assert f"RequestSent: {expected_sent}" in str(err)


@pytest.mark.asyncio
@pytest.mark.parametrize(("exc", "expected_sent"), ALL, ids=IDS)
@respx.mock
async def test_async_post_reports_request_sent(exc: httpx.HTTPError, expected_sent: bool) -> None:
    respx.post(f"{BASE}/rest/receipt").mock(side_effect=exc)
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE))
    with pytest.raises(PosApiTransportError) as info:
        await transport.send("POST", "/rest/receipt", payload={"k": "v"})
    err = info.value
    assert err.request_sent is expected_sent
    assert err.cause is exc
    assert err.__cause__ is exc


# --------------------------
# Retry loop reports the final attempt
# --------------------------


@respx.mock
def test_sync_retry_reports_final_attempt_not_sent() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.ReadTimeout("read"), httpx.ConnectError("refused")]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=2))
    with pytest.raises(PosApiTransportError) as info:
        transport.send("GET", "/x")
    assert route.call_count == 2
    assert info.value.request_sent is False
    assert isinstance(info.value.cause, httpx.ConnectError)


@respx.mock
def test_sync_retry_reports_final_attempt_sent() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.ConnectError("refused"), httpx.ReadTimeout("read")]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=2))
    with pytest.raises(PosApiTransportError) as info:
        transport.send("GET", "/x")
    assert route.call_count == 2
    assert info.value.request_sent is True
    assert isinstance(info.value.cause, httpx.ReadTimeout)


@pytest.mark.asyncio
@respx.mock
async def test_async_retry_reports_final_attempt() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.ReadTimeout("read"), httpx.ConnectTimeout("connect")]
    )
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=2))
    with pytest.raises(PosApiTransportError) as info:
        await transport.send("GET", "/x")
    assert route.call_count == 2
    assert info.value.request_sent is False
    assert isinstance(info.value.cause, httpx.ConnectTimeout)


# --------------------------
# OAuth token fetch failure: the resource request is never sent
# --------------------------

_settings = ApiClientSettings(
    base_url=BASE,
    client_id="cid",
    client_secret="sec",
    username="u",
    password="p",
    token_url=f"{BASE}/token",
)


def _auth() -> PasswordGrantAuth:
    return PasswordGrantAuth(
        settings=_settings, sync_client=httpx.Client(), async_client=httpx.AsyncClient()
    )


@respx.mock
def test_sync_token_fetch_failure_reports_not_sent() -> None:
    respx.post(f"{BASE}/token").mock(side_effect=httpx.ReadTimeout("token read"))
    resource = respx.get(f"{BASE}/api/x").mock(return_value=httpx.Response(200))
    client = httpx.Client(base_url=BASE, auth=_auth())
    transport = SyncTransport(client, retry=RetrySettings(max_retries=1))
    with pytest.raises(PosApiTransportError) as info:
        transport.send("GET", "/api/x")
    err = info.value
    assert resource.call_count == 0
    assert err.request_sent is False
    assert isinstance(err.cause, httpx.ReadTimeout)
    assert err.request is not None and err.request.url.path == "/api/x"
    assert err.request_id is not None


@pytest.mark.asyncio
@respx.mock
async def test_async_token_fetch_failure_reports_not_sent() -> None:
    respx.post(f"{BASE}/token").mock(side_effect=httpx.ConnectError("token refused"))
    resource = respx.get(f"{BASE}/api/x").mock(return_value=httpx.Response(200))
    client = httpx.AsyncClient(base_url=BASE, auth=_auth())
    transport = AsyncTransport(client, retry=RetrySettings(max_retries=1))
    with pytest.raises(PosApiTransportError) as info:
        await transport.send("GET", "/api/x")
    assert resource.call_count == 0
    assert info.value.request_sent is False
    assert isinstance(info.value.cause, httpx.ConnectError)


@respx.mock
def test_sync_token_renew_after_401_failure_reports_sent() -> None:
    """The resource request already went out once (and got 401): stay conservative."""
    token_body: dict[str, Any] = {
        "access_token": "A",
        "token_type": "Bearer",
        "expires_in": 3600,
    }
    respx.post(f"{BASE}/token").mock(
        side_effect=[httpx.Response(200, json=token_body), httpx.ReadTimeout("renew")]
    )
    resource = respx.get(f"{BASE}/api/x").mock(return_value=httpx.Response(401))
    client = httpx.Client(base_url=BASE, auth=_auth())
    transport = SyncTransport(client, retry=RetrySettings(max_retries=1))
    with pytest.raises(PosApiTransportError) as info:
        transport.send("GET", "/api/x")
    assert resource.call_count == 1
    assert info.value.request_sent is True
