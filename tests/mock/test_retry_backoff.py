"""Tests for #80 — retry hardening: full jitter, 429 retryable by default,
``Retry-After`` honoured (delta-seconds and HTTP-date), backoff cap."""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx

from ebarimt_pos_sdk.settings.retry_settings import RetrySettings
from ebarimt_pos_sdk.transport import parse_retry_after
from ebarimt_pos_sdk.transport.async_transport import AsyncTransport
from ebarimt_pos_sdk.transport.sync_transport import SyncTransport

BASE = "https://example.com"


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Capture every sleep (sync and async) instead of actually sleeping."""
    captured: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: captured.append(s))

    async def _async_sleep(s: float) -> None:
        captured.append(s)

    monkeypatch.setattr(asyncio, "sleep", _async_sleep)
    return captured


# --- settings: jitter + cap ---------------------------------------------------


def test_default_retryable_statuses_include_429() -> None:
    assert 429 in RetrySettings().retryable_statuses


def test_sleep_seconds_full_jitter_stays_within_bounds() -> None:
    s = RetrySettings(backoff_base_seconds=1.0, jitter=True)
    for attempt in range(4):
        upper = min(2**attempt, s.max_backoff_seconds)
        samples = [s.sleep_seconds(attempt) for _ in range(200)]
        assert all(0.0 <= x <= upper for x in samples)
        # Not degenerate: a 200-sample uniform draw should not all land in one place.
        assert len({round(x, 6) for x in samples}) > 1


def test_sleep_seconds_jitter_uses_random_uniform(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[float, float]] = []

    def fake_uniform(a: float, b: float) -> float:
        calls.append((a, b))
        return b / 2

    monkeypatch.setattr(random, "uniform", fake_uniform)
    s = RetrySettings(backoff_base_seconds=1.0, jitter=True)
    assert s.sleep_seconds(2) == 2.0  # upper bound 4.0, fake returns half
    assert calls == [(0.0, 4.0)]


def test_sleep_seconds_without_jitter_is_exact_exponential() -> None:
    s = RetrySettings(backoff_base_seconds=0.5, jitter=False)
    assert [s.sleep_seconds(i) for i in range(4)] == [0.5, 1.0, 2.0, 4.0]


def test_sleep_seconds_is_capped_by_max_backoff() -> None:
    s = RetrySettings(backoff_base_seconds=1.0, max_backoff_seconds=5.0, jitter=False)
    assert s.sleep_seconds(10) == 5.0
    jittered = RetrySettings(backoff_base_seconds=1.0, max_backoff_seconds=5.0, jitter=True)
    assert all(jittered.sleep_seconds(10) <= 5.0 for _ in range(100))


def test_zero_backoff_never_sleeps_even_with_jitter() -> None:
    s = RetrySettings(backoff_base_seconds=0.0, jitter=True)
    assert s.sleep_seconds(3) == 0.0


def test_retry_settings_rejects_negative_max_backoff() -> None:
    with pytest.raises(ValueError, match="max_backoff_seconds"):
        RetrySettings(max_backoff_seconds=-1)


# --- settings: Retry-After ----------------------------------------------------


def test_retry_after_overrides_backoff_and_is_not_jittered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(random, "uniform", lambda a, b: pytest.fail("must not jitter"))
    s = RetrySettings(backoff_base_seconds=1.0, jitter=True)
    assert s.sleep_seconds(0, retry_after=7.0) == 7.0


def test_retry_after_is_capped_by_max_backoff() -> None:
    s = RetrySettings(max_backoff_seconds=10.0)
    assert s.sleep_seconds(0, retry_after=3600.0) == 10.0


def test_retry_after_negative_is_clamped_to_zero() -> None:
    assert RetrySettings().sleep_seconds(0, retry_after=-5.0) == 0.0


def test_retry_after_ignored_when_disabled() -> None:
    s = RetrySettings(backoff_base_seconds=1.0, jitter=False, respect_retry_after=False)
    assert s.sleep_seconds(1, retry_after=99.0) == 2.0


# --- parse_retry_after --------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), ("", None), ("   ", None), ("120", 120.0), (" 5 ", 5.0), ("abc", None)],
)
def test_parse_retry_after_delta_seconds_and_garbage(
    value: str | None, expected: float | None
) -> None:
    assert parse_retry_after(value) == expected


def test_parse_retry_after_http_date_in_future() -> None:
    now = datetime(2026, 10, 21, 7, 28, 0, tzinfo=timezone.utc)
    assert parse_retry_after("Wed, 21 Oct 2026 07:30:00 GMT", now=now) == 120.0


def test_parse_retry_after_http_date_in_past_is_zero() -> None:
    now = datetime(2026, 10, 21, 7, 28, 0, tzinfo=timezone.utc)
    assert parse_retry_after("Wed, 21 Oct 2026 07:00:00 GMT", now=now) == 0.0


def test_parse_retry_after_http_date_uses_wall_clock_by_default() -> None:
    future = datetime.now(timezone.utc) + timedelta(seconds=90)
    value = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
    got = parse_retry_after(value)
    assert got is not None and 85.0 <= got <= 90.0


# --- transports honour Retry-After --------------------------------------------


@respx.mock
def test_sync_429_with_retry_after_seconds_is_honoured(sleeps: list[float]) -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(200, json={}),
        ]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    result = transport.send("GET", "/x")
    assert result.response.status_code == 200
    assert route.call_count == 2
    assert sleeps == [3.0]


@pytest.mark.asyncio
@respx.mock
async def test_async_503_with_retry_after_http_date_is_honoured(sleeps: list[float]) -> None:
    future = datetime.now(timezone.utc) + timedelta(seconds=4)
    respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(
                503, headers={"Retry-After": future.strftime("%a, %d %b %Y %H:%M:%S GMT")}
            ),
            httpx.Response(200, json={}),
        ]
    )
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE), retry=RetrySettings(max_retries=3))
    await transport.send("GET", "/x")
    assert len(sleeps) == 1 and 2.5 <= sleeps[0] <= 4.0


@respx.mock
def test_sync_unparseable_retry_after_falls_back_to_backoff(sleeps: list[float]) -> None:
    respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(503, headers={"Retry-After": "soon"}),
            httpx.Response(200, json={}),
        ]
    )
    transport = SyncTransport(
        httpx.Client(base_url=BASE),
        retry=RetrySettings(max_retries=3, backoff_base_seconds=0.25, jitter=False),
    )
    transport.send("GET", "/x")
    assert sleeps == [0.25]


@respx.mock
def test_sync_retry_after_capped_by_max_backoff(sleeps: list[float]) -> None:
    respx.get(f"{BASE}/x").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "600"}),
            httpx.Response(200, json={}),
        ]
    )
    transport = SyncTransport(
        httpx.Client(base_url=BASE),
        retry=RetrySettings(max_retries=3, max_backoff_seconds=15.0),
    )
    transport.send("GET", "/x")
    assert sleeps == [15.0]


@respx.mock
def test_sync_network_error_backoff_is_jittered(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.123)
    respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.ConnectError("boom"), httpx.Response(200, json={})]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))
    transport.send("GET", "/x")
    assert sleeps == [0.123]
