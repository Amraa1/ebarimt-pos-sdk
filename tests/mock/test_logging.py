from __future__ import annotations

import asyncio
import logging
import time

import httpx
import pytest
import respx

from ebarimt_pos_sdk.errors import PosApiTransportError
from ebarimt_pos_sdk.settings.retry_settings import RetrySettings
from ebarimt_pos_sdk.transport.async_transport import AsyncTransport
from ebarimt_pos_sdk.transport.sync_transport import SyncTransport

BASE = "https://example.com"
LOGGER = "ebarimt_pos_sdk"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    async def _fast_async_sleep(_s: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_async_sleep)


def _sdk_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name.startswith(LOGGER)]


def _request_ids(records: list[logging.LogRecord]) -> set[str]:
    return {r.request_id for r in records if hasattr(r, "request_id")}  # type: ignore[attr-defined]


# --------------------------
# Happy-path lifecycle lines
# --------------------------


@respx.mock
def test_sync_logs_request_and_response_at_debug(caplog: pytest.LogCaptureFixture) -> None:
    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(200, json={"ok": True}))
    transport = SyncTransport(httpx.Client(base_url=BASE))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        transport.send("GET", "/x")

    records = _sdk_records(caplog)
    messages = [r.getMessage() for r in records]
    assert any(m.startswith("→ GET") for m in messages)
    assert any(m.startswith("← 200") for m in messages)
    assert all(r.levelno == logging.DEBUG for r in records)
    # Both lines share exactly one request id.
    assert len(_request_ids(records)) == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_logs_request_and_response_at_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(200, json={"ok": True}))
    transport = AsyncTransport(httpx.AsyncClient(base_url=BASE))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        await transport.send("GET", "/x")

    records = _sdk_records(caplog)
    messages = [r.getMessage() for r in records]
    assert any(m.startswith("→ GET") for m in messages)
    assert any(m.startswith("← 200") for m in messages)
    assert len(_request_ids(records)) == 1


# --------------------------
# Retry → WARNING, shared id
# --------------------------


@respx.mock
def test_retry_emits_warning_and_shares_request_id(caplog: pytest.LogCaptureFixture) -> None:
    respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200, json={})]
    )
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=3))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        transport.send("GET", "/x")

    records = _sdk_records(caplog)
    warnings = [r for r in records if r.levelno == logging.WARNING]
    # Two retried attempts (503, 503) → two WARNING lines; the third succeeds.
    assert len(warnings) == 2
    assert all(w.getMessage().startswith("retry ") for w in warnings)
    # Every line for this logical request shares one id.
    assert len(_request_ids(records)) == 1


# --------------------------
# No log-and-raise
# --------------------------


@respx.mock
def test_failure_raises_without_error_record(caplog: pytest.LogCaptureFixture) -> None:
    respx.get(f"{BASE}/x").mock(side_effect=httpx.ConnectError("boom"))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=2))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        with pytest.raises(PosApiTransportError):
            transport.send("GET", "/x")

    records = _sdk_records(caplog)
    # The SDK never logs the failure itself — it only raises.
    assert not any(r.levelno >= logging.ERROR for r in records)


@respx.mock
def test_raised_error_carries_request_id(caplog: pytest.LogCaptureFixture) -> None:
    respx.get(f"{BASE}/x").mock(side_effect=httpx.ConnectError("boom"))
    transport = SyncTransport(httpx.Client(base_url=BASE), retry=RetrySettings(max_retries=2))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        with pytest.raises(PosApiTransportError) as exc_info:
            transport.send("GET", "/x")

    err = exc_info.value
    assert err.request_id is not None
    # The id on the exception matches the id stamped on every log line.
    assert _request_ids(_sdk_records(caplog)) == {err.request_id}


# --------------------------
# Redaction (security-critical)
# --------------------------


@respx.mock
def test_secrets_never_appear_in_log_records(caplog: pytest.LogCaptureFixture) -> None:
    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(200, json={}))
    transport = SyncTransport(httpx.Client(base_url=BASE))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        transport.send(
            "GET",
            "/x",
            params={"access_token": "QUERYSECRET"},
            headers={"Authorization": "Bearer HEADERSECRET"},
        )

    haystack = "\n".join(r.getMessage() for r in _sdk_records(caplog))
    assert "QUERYSECRET" not in haystack  # sensitive query param is masked
    assert "HEADERSECRET" not in haystack  # headers are never logged
    assert "access_token=***" in haystack


@respx.mock
def test_tin_in_path_is_not_redacted(caplog: pytest.LogCaptureFixture) -> None:
    """TINs are public identifiers — path segments are intentionally left intact."""
    respx.get(f"{BASE}/api/info/9988776655").mock(return_value=httpx.Response(200, json={}))
    transport = SyncTransport(httpx.Client(base_url=BASE))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        transport.send("GET", "/api/info/9988776655")

    haystack = "\n".join(r.getMessage() for r in _sdk_records(caplog))
    assert "9988776655" in haystack


# --------------------------
# Quiet by default
# --------------------------


@respx.mock
def test_no_records_when_level_above_debug(caplog: pytest.LogCaptureFixture) -> None:
    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(200, json={}))
    transport = SyncTransport(httpx.Client(base_url=BASE))

    with caplog.at_level(logging.INFO, logger=LOGGER):
        transport.send("GET", "/x")

    # Lifecycle lines are DEBUG; nothing should surface at INFO+.
    assert _sdk_records(caplog) == []
