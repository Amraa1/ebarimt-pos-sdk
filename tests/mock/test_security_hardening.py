"""Regression tests for the 0.4.2 security hardening: secrets must not leak
through ``repr()``, URL userinfo must be redacted, HTTP-error fallback messages
must not echo raw query params, and disabling TLS must be loud."""

from __future__ import annotations

import logging

import httpx
import pytest
import respx

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings
from ebarimt_pos_sdk._redaction import redact_url
from ebarimt_pos_sdk.auth import OAuth2Token
from ebarimt_pos_sdk.errors import PosApiHttpError
from ebarimt_pos_sdk.settings import ApiClientSettings

SECRET = "s3cr3t-p4ssw0rd"
TOKEN = "eyJ-very-secret-access-token"


def test_api_client_settings_repr_hides_secrets() -> None:
    s = ApiClientSettings(
        base_url="https://example.com",
        token_url="https://example.com/token",
        client_id="cid",
        client_secret=SECRET,
        username="user",
        password=SECRET,
    )
    text = repr(s)
    assert SECRET not in text
    assert "cid" in text  # non-secret fields still shown
    # The values themselves remain accessible.
    assert s.password == SECRET
    assert s.client_secret == SECRET


def test_oauth2_token_repr_hides_token_material() -> None:
    tok = OAuth2Token.from_authlib(
        {
            "access_token": TOKEN,
            "refresh_token": "refresh-" + TOKEN,
            "token_type": "Bearer",
            "expires_in": 300,
            "expires_at": 1_900_000_000,
        }
    )
    text = repr(tok)
    assert TOKEN not in text
    assert "refresh-" not in text
    assert "Bearer" in text
    assert tok.access_token == TOKEN


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://user:pw@proxy.example.com:8080/p", "https://***@proxy.example.com:8080/p"),
        ("https://user@h.example.com/p?token=abc", "https://***@h.example.com/p?token=***"),
        ("https://h.example.com/p?x=1", "https://h.example.com/p?x=1"),
    ],
)
def test_redact_url_masks_userinfo(raw: str, expected: str) -> None:
    assert redact_url(httpx.URL(raw)) == expected
    assert "pw" not in redact_url(httpx.URL(raw)).split("@")[0]


@respx.mock
def test_http_error_fallback_message_uses_redacted_url() -> None:
    respx.get("https://api.example.com/rest/info").mock(
        return_value=httpx.Response(404, text="<html>Not Found</html>")
    )
    settings = RestClientSettings(base_url="https://api.example.com")
    with EbarimtRestClient(settings) as client:
        with pytest.raises(PosApiHttpError) as exc_info:
            client.info.read(headers={"X-Test": "1"})
    assert "Http Error 404" in exc_info.value.message
    assert "GET https://api.example.com/rest/info" in exc_info.value.message
    # Fallback must not fall back to httpx's raw Request repr.
    assert "Request(" not in exc_info.value.message


def test_verify_tls_false_on_https_warns(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="ebarimt_pos_sdk"):
        with EbarimtRestClient(
            RestClientSettings(base_url="https://pos.example.com", verify_tls=False)
        ):
            pass
    assert any("TLS certificate verification is DISABLED" in r.message for r in caplog.records)


def test_verify_tls_false_on_http_is_silent(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="ebarimt_pos_sdk"):
        with EbarimtRestClient(
            RestClientSettings(base_url="http://localhost:1234", verify_tls=False)
        ):
            pass
    assert not [r for r in caplog.records if "DISABLED" in r.message]
