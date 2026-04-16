from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

import httpx
import pytest

# ✅ Update these imports to your real paths
from ebarimt_pos_sdk.auth.password_grant import PasswordGrantAuth
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
    auth = PasswordGrantAuth(
        settings=settings, sync_client=sync, async_client=async_client, skew_seconds=0
    )

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
async def test_async_auth_flow_injects_authorization_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
async def test_async_concurrent_requests_fetch_token_only_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


# --------------------------
# Token refresh tests
# --------------------------

settings_with_refresh = ApiClientSettings(
    base_url="https://example.com",
    client_id="cid",
    client_secret="sec",
    username="u",
    password="p",
    token_url="https://example.com/token",
    refresh_url="https://example.com/refresh",
)


def make_token_with_refresh(
    *, access: str, expires_at: int, refresh: str = "REFRESH", refresh_expires_in: int = 3600
) -> dict[str, Any]:
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": max(0, int(expires_at - time.time())),
        "expires_at": int(expires_at),
        "refresh_token": refresh,
        "refresh_expires_in": refresh_expires_in,
    }


def test_sync_refreshes_token_when_access_expired_and_refresh_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expired access + valid refresh -> _refresh_token_sync called, fetch_token NOT called again."""
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(
        settings=settings_with_refresh,
        sync_client=sync,
        async_client=async_client,
        skew_seconds=0,
    )

    fetch_calls = 0
    refresh_calls = 0

    def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal fetch_calls
        fetch_calls += 1
        return make_token_with_refresh(access="OLD", expires_at=int(time.time()) - 1, refresh="R1")

    def fake_refresh_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal refresh_calls
        refresh_calls += 1
        assert kwargs["refresh_token"] == "R1"
        return make_token_with_refresh(
            access="REFRESHED", expires_at=int(time.time()) + 3600, refresh="R2"
        )

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]
    monkeypatch.setattr(auth._oauth_sync, "refresh_token", fake_refresh_token)  # type: ignore[attr-defined]

    req1 = httpx.Request("GET", "https://example.com/data")
    r1 = next(auth.auth_flow(req1))
    assert r1.headers["Authorization"] == "Bearer OLD"

    req2 = httpx.Request("GET", "https://example.com/data")
    r2 = next(auth.auth_flow(req2))
    assert r2.headers["Authorization"] == "Bearer REFRESHED"
    assert fetch_calls == 1
    assert refresh_calls == 1


def test_sync_falls_back_to_fetch_when_refresh_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refresh raises -> _ensure_token_sync surfaces PosApiTransportError, next call re-fetches."""
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(
        settings=settings_with_refresh,
        sync_client=sync,
        async_client=async_client,
        skew_seconds=0,
    )

    fetch_seq = [
        make_token_with_refresh(access="OLD", expires_at=int(time.time()) - 1, refresh="R1"),
        make_token_with_refresh(access="NEW", expires_at=int(time.time()) + 3600, refresh="R2"),
    ]
    fetch_idx = 0

    def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal fetch_idx
        t = fetch_seq[fetch_idx]
        fetch_idx += 1
        return t

    def failing_refresh(**kwargs: Any) -> dict[str, Any]:
        raise httpx.HTTPError("refresh blew up")

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]
    monkeypatch.setattr(auth._oauth_sync, "refresh_token", failing_refresh)  # type: ignore[attr-defined]

    next(auth.auth_flow(httpx.Request("GET", "https://example.com/data")))

    from ebarimt_pos_sdk.errors import PosApiTransportError

    with pytest.raises(PosApiTransportError):
        next(auth.auth_flow(httpx.Request("GET", "https://example.com/data")))

    auth._token = None  # type: ignore[attr-defined]
    r3 = next(auth.auth_flow(httpx.Request("GET", "https://example.com/data")))
    assert r3.headers["Authorization"] == "Bearer NEW"
    assert fetch_idx == 2


def test_sync_does_not_refresh_when_token_still_fresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cached fresh token -> neither fetch nor refresh called on subsequent requests."""
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(
        settings=settings_with_refresh,
        sync_client=sync,
        async_client=async_client,
        skew_seconds=0,
    )

    fetch_calls = 0
    refresh_calls = 0

    def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal fetch_calls
        fetch_calls += 1
        return make_token_with_refresh(
            access="FRESH", expires_at=int(time.time()) + 3600, refresh="R1"
        )

    def fake_refresh_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal refresh_calls
        refresh_calls += 1
        return make_token_with_refresh(access="X", expires_at=int(time.time()) + 3600, refresh="R2")

    monkeypatch.setattr(auth._oauth_sync, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]
    monkeypatch.setattr(auth._oauth_sync, "refresh_token", fake_refresh_token)  # type: ignore[attr-defined]

    for _ in range(3):
        next(auth.auth_flow(httpx.Request("GET", "https://example.com/data")))

    assert fetch_calls == 1
    assert refresh_calls == 0


@pytest.mark.asyncio
async def test_async_refreshes_token_when_access_expired_and_refresh_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(
        settings=settings_with_refresh,
        sync_client=sync,
        async_client=async_client,
        skew_seconds=0,
    )

    fetch_calls = 0
    refresh_calls = 0

    async def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal fetch_calls
        fetch_calls += 1
        return make_token_with_refresh(access="OLD", expires_at=int(time.time()) - 1, refresh="R1")

    async def fake_refresh_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal refresh_calls
        refresh_calls += 1
        assert kwargs["refresh_token"] == "R1"
        return make_token_with_refresh(
            access="REFRESHED", expires_at=int(time.time()) + 3600, refresh="R2"
        )

    monkeypatch.setattr(auth._oauth_async, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]
    monkeypatch.setattr(auth._oauth_async, "refresh_token", fake_refresh_token)  # type: ignore[attr-defined]

    r1 = await auth.async_auth_flow(httpx.Request("GET", "https://example.com/data")).__anext__()
    assert r1.headers["Authorization"] == "Bearer OLD"

    r2 = await auth.async_auth_flow(httpx.Request("GET", "https://example.com/data")).__anext__()
    assert r2.headers["Authorization"] == "Bearer REFRESHED"
    assert fetch_calls == 1
    assert refresh_calls == 1


@pytest.mark.asyncio
async def test_async_falls_back_to_fetch_when_refresh_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync = httpx.Client()
    async_client = httpx.AsyncClient()
    auth = PasswordGrantAuth(
        settings=settings_with_refresh,
        sync_client=sync,
        async_client=async_client,
        skew_seconds=0,
    )

    fetch_seq = [
        make_token_with_refresh(access="OLD", expires_at=int(time.time()) - 1, refresh="R1"),
        make_token_with_refresh(access="NEW", expires_at=int(time.time()) + 3600, refresh="R2"),
    ]
    fetch_idx = 0

    async def fake_fetch_token(**kwargs: Any) -> dict[str, Any]:
        nonlocal fetch_idx
        t = fetch_seq[fetch_idx]
        fetch_idx += 1
        return t

    async def failing_refresh(**kwargs: Any) -> dict[str, Any]:
        raise httpx.HTTPError("refresh blew up")

    monkeypatch.setattr(auth._oauth_async, "fetch_token", fake_fetch_token)  # type: ignore[attr-defined]
    monkeypatch.setattr(auth._oauth_async, "refresh_token", failing_refresh)  # type: ignore[attr-defined]

    await auth.async_auth_flow(httpx.Request("GET", "https://example.com/data")).__anext__()

    from ebarimt_pos_sdk.errors import PosApiTransportError

    with pytest.raises(PosApiTransportError):
        await auth.async_auth_flow(httpx.Request("GET", "https://example.com/data")).__anext__()

    auth._token = None  # type: ignore[attr-defined]
    r3 = await auth.async_auth_flow(httpx.Request("GET", "https://example.com/data")).__anext__()
    assert r3.headers["Authorization"] == "Bearer NEW"
    assert fetch_idx == 2
