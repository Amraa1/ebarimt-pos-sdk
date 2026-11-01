"""Tests for #81 — one transparent renew-and-retry when the server answers 401
to a token the client still considered valid."""

from __future__ import annotations

import time
from typing import Any

import httpx
import pytest

from ebarimt_pos_sdk.auth.password_grant import PasswordGrantAuth
from ebarimt_pos_sdk.settings import ApiClientSettings

SETTINGS = ApiClientSettings(
    base_url="https://example.com",
    client_id="cid",
    client_secret="sec",
    username="u",
    password="p",
    token_url="https://example.com/token",
)
SETTINGS_WITH_REFRESH = ApiClientSettings(
    base_url="https://example.com",
    client_id="cid",
    client_secret="sec",
    username="u",
    password="p",
    token_url="https://example.com/token",
    refresh_url="https://example.com/token",
)


def tok(access: str, *, refresh: str | None = None, ttl: int = 3600) -> dict[str, Any]:
    now = int(time.time())
    d: dict[str, Any] = {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": ttl,
        "expires_at": now + ttl,
    }
    if refresh is not None:
        d["refresh_token"] = refresh
        d["refresh_expires_in"] = ttl * 2
    return d


def make_auth(settings: ApiClientSettings = SETTINGS) -> PasswordGrantAuth:
    return PasswordGrantAuth(
        settings=settings, sync_client=httpx.Client(), async_client=httpx.AsyncClient()
    )


def req() -> httpx.Request:
    return httpx.Request("POST", "https://example.com/data", json={"k": "v"})


# --- sync ---------------------------------------------------------------------


def test_sync_non_401_response_ends_flow_without_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = make_auth()
    fetches = 0

    def fetch(**kw: Any) -> dict[str, Any]:
        nonlocal fetches
        fetches += 1
        return tok("T1")

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fetch)
    flow = auth.auth_flow(req())
    r1 = next(flow)
    assert r1.headers["Authorization"] == "Bearer T1"
    with pytest.raises(StopIteration):
        flow.send(httpx.Response(200))
    assert fetches == 1


def test_sync_401_renews_via_password_grant_and_retries_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = make_auth()
    seq = iter([tok("T1"), tok("T2")])
    monkeypatch.setattr(auth._oauth_sync, "fetch_token", lambda **kw: next(seq))

    flow = auth.auth_flow(req())
    r1 = next(flow)
    assert r1.headers["Authorization"] == "Bearer T1"
    r2 = flow.send(httpx.Response(401))
    assert r2.headers["Authorization"] == "Bearer T2"
    assert r2 is r1  # same request object re-yielded, body intact
    assert r2.content == b'{"k":"v"}'
    with pytest.raises(StopIteration):
        flow.send(httpx.Response(200))


def test_sync_second_401_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard against an infinite loop on a genuinely invalid credential."""
    auth = make_auth()
    fetches = 0

    def fetch(**kw: Any) -> dict[str, Any]:
        nonlocal fetches
        fetches += 1
        return tok(f"T{fetches}")

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fetch)
    flow = auth.auth_flow(req())
    next(flow)
    flow.send(httpx.Response(401))
    with pytest.raises(StopIteration):
        flow.send(httpx.Response(401))
    assert fetches == 2


def test_sync_401_prefers_refresh_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = make_auth(SETTINGS_WITH_REFRESH)
    fetches = 0
    refreshes = 0

    def fetch(**kw: Any) -> dict[str, Any]:
        nonlocal fetches
        fetches += 1
        return tok("T1", refresh="R1")

    def refresh(**kw: Any) -> dict[str, Any]:
        nonlocal refreshes
        refreshes += 1
        assert kw["refresh_token"] == "R1"
        return tok("T2", refresh="R2")

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fetch)
    monkeypatch.setattr(auth._oauth_sync, "refresh_token", refresh)
    flow = auth.auth_flow(req())
    next(flow)
    r2 = flow.send(httpx.Response(401))
    assert r2.headers["Authorization"] == "Bearer T2"
    assert (fetches, refreshes) == (1, 1)


def test_sync_401_falls_back_to_password_grant_when_refresh_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A revoked session usually kills the refresh token too."""
    auth = make_auth(SETTINGS_WITH_REFRESH)
    seq = iter([tok("T1", refresh="R1"), tok("T2", refresh="R2")])
    monkeypatch.setattr(auth._oauth_sync, "fetch_token", lambda **kw: next(seq))

    def refresh(**kw: Any) -> dict[str, Any]:
        raise httpx.HTTPStatusError(
            "400", request=httpx.Request("POST", "https://x"), response=httpx.Response(400)
        )

    monkeypatch.setattr(auth._oauth_sync, "refresh_token", refresh)
    flow = auth.auth_flow(req())
    next(flow)
    r2 = flow.send(httpx.Response(401))
    assert r2.headers["Authorization"] == "Bearer T2"


def test_sync_401_reuses_token_already_renewed_by_another_caller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ebarimt_pos_sdk.auth import OAuth2Token

    auth = make_auth()
    fetches = 0

    def fetch(**kw: Any) -> dict[str, Any]:
        nonlocal fetches
        fetches += 1
        return tok("T1")

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fetch)
    flow = auth.auth_flow(req())
    next(flow)
    # Simulate a concurrent caller having already replaced the token.
    auth._token = OAuth2Token.from_authlib(tok("FRESH"))
    r2 = flow.send(httpx.Response(401))
    assert r2.headers["Authorization"] == "Bearer FRESH"
    assert fetches == 1


def test_sync_end_to_end_with_httpx_mock_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drive the real httpx Auth machinery: first call 401, retry 200."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["Authorization"])
        return httpx.Response(401) if len(seen) == 1 else httpx.Response(200, json={"ok": 1})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    auth = PasswordGrantAuth(
        settings=SETTINGS, sync_client=client, async_client=httpx.AsyncClient()
    )
    seq = iter([tok("T1"), tok("T2")])
    monkeypatch.setattr(auth._oauth_sync, "fetch_token", lambda **kw: next(seq))

    resp = client.post("https://example.com/data", json={"k": "v"}, auth=auth)
    assert resp.status_code == 200
    assert seen == ["Bearer T1", "Bearer T2"]


# --- async --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_401_renews_and_retries_once(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = make_auth()
    seq = iter([tok("T1"), tok("T2")])

    async def fetch(**kw: Any) -> dict[str, Any]:
        return next(seq)

    monkeypatch.setattr(auth._oauth_async, "fetch_token", fetch)
    flow = auth.async_auth_flow(req())
    r1 = await flow.__anext__()
    assert r1.headers["Authorization"] == "Bearer T1"
    r2 = await flow.asend(httpx.Response(401))
    assert r2.headers["Authorization"] == "Bearer T2"
    with pytest.raises(StopAsyncIteration):
        await flow.asend(httpx.Response(401))


@pytest.mark.asyncio
async def test_async_401_prefers_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = make_auth(SETTINGS_WITH_REFRESH)

    async def fetch(**kw: Any) -> dict[str, Any]:
        return tok("T1", refresh="R1")

    async def refresh(**kw: Any) -> dict[str, Any]:
        assert kw["refresh_token"] == "R1"
        return tok("T2", refresh="R2")

    monkeypatch.setattr(auth._oauth_async, "fetch_token", fetch)
    monkeypatch.setattr(auth._oauth_async, "refresh_token", refresh)
    flow = auth.async_auth_flow(req())
    await flow.__anext__()
    r2 = await flow.asend(httpx.Response(401))
    assert r2.headers["Authorization"] == "Bearer T2"


@pytest.mark.asyncio
async def test_async_end_to_end_with_httpx_mock_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["Authorization"])
        return httpx.Response(401) if len(seen) == 1 else httpx.Response(200, json={"ok": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    auth = PasswordGrantAuth(settings=SETTINGS, sync_client=httpx.Client(), async_client=client)
    seq = iter([tok("T1"), tok("T2")])

    async def fetch(**kw: Any) -> dict[str, Any]:
        return next(seq)

    monkeypatch.setattr(auth._oauth_async, "fetch_token", fetch)
    resp = await client.post("https://example.com/data", json={"k": "v"}, auth=auth)
    assert resp.status_code == 200
    assert seen == ["Bearer T1", "Bearer T2"]
