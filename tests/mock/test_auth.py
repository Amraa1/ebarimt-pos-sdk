from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx
import pytest

# ✅ Update these imports to your real paths
from ebarimt_pos_sdk.auth.password_grant import PasswordGrantAuth
from ebarimt_pos_sdk.auth.token import OAuth2Token
from ebarimt_pos_sdk.settings import ApiClientSettings


# --------------------------
# Helpers
# --------------------------

settings = ApiClientSettings(
        base_url="https://example.com",
        client_id="cid",
        client_secret="sec",
        username="u",
        password="p",
        token_url="https://example.com/token",
    )

def make_token(*, access: str, expires_at: int) -> dict[str, Any]:
    """
    Return an Authlib-like token dict.
    PasswordGrantAuth -> OAuth2Token.from_authlib() consumes this.
    """
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": max(0, int(expires_at - time.time())),
        "expires_at": int(expires_at),
    }


# --------------------------
# Sync tests
# --------------------------

def test_auth_flow_injects_authorization_header_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensures auth_flow sets Authorization header using fetched token.
    """
    settings = ApiClientSettings(
        base_url="https://example.com",
        client_id="cid",
        client_secret="sec",
        username="u",
        password="p",
        token_url="https://example.com/token",
    )

    sync = httpx.Client()
    async_client = httpx.AsyncClient()

    auth = PasswordGrantAuth(settings=settings, sync_client=sync, async_client=async_client)

    # Mock token fetch (avoid touching Authlib internals)
    expires_at = int(time.time()) + 3600
    monkeypatch.setattr(
        auth._oauth_sync,  # type: ignore[attr-defined]
        "fetch_token",
        lambda **kwargs: make_token(access="SYNC_TOKEN", expires_at=expires_at),
    )

    req = httpx.Request("GET", "https://example.com/data")
    flow = auth.auth_flow(req)

    req2 = next(flow)  # the yielded request
    assert req2.headers["Authorization"] == "Bearer SYNC_TOKEN"


def test_sync_concurrent_requests_fetch_token_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    If many threads hit auth_flow at once with no cached token, token should be fetched once
    due to _sync_lock + double-check.
    """
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(settings=settings, sync_client=sync, async_client=async_client)

    calls = 0
    calls_lock = threading.Lock()

    def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        with calls_lock:
            calls += 1
        # Make it slow so threads overlap (exposes race bugs)
        time.sleep(0.05)
        expires_at = int(time.time()) + 3600
        return make_token(access="SYNC_TOKEN", expires_at=expires_at)

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]

    def worker() -> None:
        req = httpx.Request("GET", "https://example.com/data")
        req2 = next(auth.auth_flow(req))
        assert req2.headers["Authorization"].startswith("Bearer ")

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert calls == 1, f"Expected 1 token fetch, got {calls}"


def test_sync_fetches_new_token_when_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    If cached token is expired, _ensure_token_sync should fetch a new one.
    """
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(settings=settings, sync_client=sync, async_client=async_client, skew_seconds=0)

    # First call returns already-expired token; second returns valid token.
    seq = [
        make_token(access="OLD", expires_at=int(time.time()) - 1),
        make_token(access="NEW", expires_at=int(time.time()) + 3600),
    ]
    idx = 0

    def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal idx
        t = seq[idx]
        idx += 1
        return t

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]

    # First request: sees no token -> fetch OLD (expired immediately, but still used once)
    req1 = httpx.Request("GET", "https://example.com/data")
    r1 = next(auth.auth_flow(req1))
    assert r1.headers["Authorization"] == "Bearer OLD"

    # Second request: token is expired -> must fetch NEW
    req2 = httpx.Request("GET", "https://example.com/data")
    r2 = next(auth.auth_flow(req2))
    assert r2.headers["Authorization"] == "Bearer NEW"
    assert idx == 2


# --------------------------
# Async tests
# --------------------------

@pytest.mark.asyncio
async def test_async_auth_flow_injects_authorization_header(monkeypatch: pytest.MonkeyPatch) -> None:
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(settings=settings, sync_client=sync, async_client=async_client)

    async def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        expires_at = int(time.time()) + 3600
        return make_token(access="ASYNC_TOKEN", expires_at=expires_at)

    monkeypatch.setattr(auth._oauth_async, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]

    req = httpx.Request("GET", "https://example.com/data")
    agen = auth.async_auth_flow(req)

    req2 = await agen.__anext__()
    assert req2.headers["Authorization"] == "Bearer ASYNC_TOKEN"


@pytest.mark.asyncio
async def test_async_concurrent_requests_fetch_token_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    If many async tasks hit async_auth_flow at once, token should be fetched once
    due to _async_lock + double-check.
    """
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(settings=settings, sync_client=sync, async_client=async_client)

    calls = 0
    calls_lock = asyncio.Lock()

    async def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        async with calls_lock:
            calls += 1
        # Make it slow so tasks overlap (exposes race bugs)
        await asyncio.sleep(0.05)
        expires_at = int(time.time()) + 3600
        return make_token(access="ASYNC_TOKEN", expires_at=expires_at)

    monkeypatch.setattr(auth._oauth_async, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]

    async def worker() -> None:
        req = httpx.Request("GET", "https://example.com/data")
        agen = auth.async_auth_flow(req)
        req2 = await agen.__anext__()
        assert req2.headers["Authorization"].startswith("Bearer ")

    await asyncio.gather(*(worker() for _ in range(30)))
    assert calls == 1, f"Expected 1 token fetch, got {calls}"