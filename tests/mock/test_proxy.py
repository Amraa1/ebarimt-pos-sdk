from __future__ import annotations

from typing import Any

import httpx
import pytest

from ebarimt_pos_sdk import EbarimtApiClient, Environment, create_api_settings


def _settings() -> Any:
    return create_api_settings(Environment.STAGING)


def _spy_proxy(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Record the `proxy` kwarg passed to the httpx client constructors."""
    captured: dict[str, object] = {}
    real_sync = httpx.Client
    real_async = httpx.AsyncClient

    def spy_sync(*args: Any, **kwargs: Any) -> httpx.Client:
        captured["sync"] = kwargs.get("proxy")
        return real_sync(*args, **kwargs)

    def spy_async(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        captured["async"] = kwargs.get("proxy")
        return real_async(*args, **kwargs)

    monkeypatch.setattr("ebarimt_pos_sdk.clients.base_client.httpx.Client", spy_sync)
    monkeypatch.setattr("ebarimt_pos_sdk.clients.base_client.httpx.AsyncClient", spy_async)
    return captured


def test_proxy_string_forwarded_to_both_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _spy_proxy(monkeypatch)
    proxy = "http://user:pass@mn-proxy:8080"

    with EbarimtApiClient(_settings(), proxy=proxy):
        pass

    assert captured["sync"] == proxy
    assert captured["async"] == proxy


def test_proxy_object_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _spy_proxy(monkeypatch)
    proxy = httpx.Proxy("http://mn-proxy:8080")

    with EbarimtApiClient(_settings(), proxy=proxy):
        pass

    assert captured["sync"] is proxy


def test_proxy_defaults_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _spy_proxy(monkeypatch)

    with EbarimtApiClient(_settings()):
        pass

    assert captured["sync"] is None


def test_proxy_with_injected_client_raises() -> None:
    injected = httpx.Client()
    try:
        with pytest.raises(ValueError, match="proxy cannot be combined"):
            EbarimtApiClient(_settings(), sync_client=injected, proxy="http://mn-proxy:8080")
    finally:
        injected.close()
