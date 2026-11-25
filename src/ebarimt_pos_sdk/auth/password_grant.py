from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncGenerator, Generator
from typing import Any

import httpx

from ..errors import PosApiTransportError
from ..settings import ApiClientSettings
from .token import OAuth2Token

_TOKEN_TRANSPORT_EXCEPTIONS = (httpx.HTTPError, OSError, ValueError)

# The base ``httpx.Auth`` passes the request through untouched. Passing it
# explicitly keeps an injected client's own default auth off the token request,
# and stops the token request from ever running through PasswordGrantAuth.
_NO_AUTH = httpx.Auth()


def _password_form(
    settings: ApiClientSettings, *, username: str | None, password: str | None, scope: str | None
) -> dict[str, str]:
    form = {"grant_type": "password", "username": username or "", "password": password or ""}
    return _with_client_credentials(form, settings, scope=scope)


def _refresh_form(settings: ApiClientSettings, *, refresh_token: str | None) -> dict[str, str]:
    form = {"grant_type": "refresh_token", "refresh_token": refresh_token or ""}
    return _with_client_credentials(form, settings, scope=None)


def _with_client_credentials(
    form: dict[str, str], settings: ApiClientSettings, *, scope: str | None
) -> dict[str, str]:
    # Client credentials go in the form body (``client_secret_post``), which
    # Keycloak accepts for both public and confidential clients.
    if settings.client_id:
        form["client_id"] = settings.client_id
    if settings.client_secret:
        form["client_secret"] = settings.client_secret
    if scope:
        form["scope"] = scope
    return form


def _parse_token_response(response: httpx.Response) -> dict[str, Any]:
    """Return the token response as a dict, or raise without echoing token material.

    Only the OAuth ``error`` / ``error_description`` fields of a rejection are
    surfaced; the body of a successful response holds the tokens and is never
    put into an error message.
    """
    if response.is_success:
        token = response.json()
        if not isinstance(token, dict) or not token.get("access_token"):
            raise ValueError("token response has no access_token")
        return token
    detail = ""
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and body.get("error"):
        detail = f": {body['error']}"
        if body.get("error_description"):
            detail += f" ({body['error_description']})"
    raise httpx.HTTPStatusError(
        f"token endpoint returned HTTP {response.status_code}{detail}",
        request=response.request,
        response=response,
    )


class _TokenEndpoint:
    """Password and refresh grants, sent through the SDK's own ``httpx.Client``
    so the token request honours its proxy, TLS, timeout and transport."""

    def __init__(self, settings: ApiClientSettings, http: httpx.Client) -> None:
        self._settings = settings
        self._http = http

    def _post(self, url: str | None, form: dict[str, str]) -> dict[str, Any]:
        if not url:
            raise ValueError("token_url is not configured")
        return _parse_token_response(self._http.post(url, data=form, auth=_NO_AUTH))

    def fetch_token(
        self,
        *,
        url: str | None,
        username: str | None,
        password: str | None,
        scope: str | None = None,
    ) -> dict[str, Any]:
        form = _password_form(self._settings, username=username, password=password, scope=scope)
        return self._post(url, form)

    def refresh_token(self, *, url: str | None, refresh_token: str | None) -> dict[str, Any]:
        return self._post(url, _refresh_form(self._settings, refresh_token=refresh_token))


class _AsyncTokenEndpoint:
    """Async twin of :class:`_TokenEndpoint`."""

    def __init__(self, settings: ApiClientSettings, http: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http

    async def _post(self, url: str | None, form: dict[str, str]) -> dict[str, Any]:
        if not url:
            raise ValueError("token_url is not configured")
        return _parse_token_response(await self._http.post(url, data=form, auth=_NO_AUTH))

    async def fetch_token(
        self,
        *,
        url: str | None,
        username: str | None,
        password: str | None,
        scope: str | None = None,
    ) -> dict[str, Any]:
        form = _password_form(self._settings, username=username, password=password, scope=scope)
        return await self._post(url, form)

    async def refresh_token(self, *, url: str | None, refresh_token: str | None) -> dict[str, Any]:
        return await self._post(url, _refresh_form(self._settings, refresh_token=refresh_token))


class PasswordGrantAuth(httpx.Auth):
    """
    OAuth2 Password Grant auth for httpx.Client and httpx.AsyncClient.

    Constraints:
      - Token requests go through the same httpx clients the API client uses,
        so they honour its proxy, TLS verification, timeout and any injected
        client.
      - Token calls bypass auth (a no-op ``httpx.Auth``) to avoid recursion.

    401 handling: if the server rejects a token the client still considers
    valid (revocation, clock drift, server-side session purge), the flow
    renews the token once — refresh if possible, otherwise a fresh password
    grant — and re-sends the request exactly once. A second 401 is returned
    to the caller as-is, so a genuinely invalid credential cannot loop.
    """

    requires_request_body = True

    def __init__(
        self,
        *,
        settings: ApiClientSettings,
        sync_client: httpx.Client,
        async_client: httpx.AsyncClient,
        skew_seconds: float = 30,
    ) -> None:
        self._settings = settings
        self._sync_http = sync_client
        self._async_http = async_client
        self._skew = skew_seconds

        self._token: OAuth2Token | None = None
        self._sync_lock = threading.Lock()
        self._async_lock = asyncio.Lock()
        self._oauth_sync = _TokenEndpoint(settings, sync_client)
        self._oauth_async = _AsyncTokenEndpoint(settings, async_client)

    def _fetch_token_sync(self) -> OAuth2Token:
        try:
            token_dict = self._oauth_sync.fetch_token(
                url=self._settings.normalized_token_url,
                username=self._settings.username,
                password=self._settings.password,
                scope=self._settings.scope,
            )
            return OAuth2Token.from_authlib(token_dict)
        except _TOKEN_TRANSPORT_EXCEPTIONS as exc:
            raise PosApiTransportError(f"Token fetch failed: {exc}", cause=exc) from exc

    def _refresh_token_sync(self, current_token: OAuth2Token) -> OAuth2Token:
        try:
            token_dict = self._oauth_sync.refresh_token(
                url=self._settings.normalized_refresh_url,
                refresh_token=current_token.refresh_token,
            )
            return OAuth2Token.from_authlib(token_dict)
        except _TOKEN_TRANSPORT_EXCEPTIONS as exc:
            raise PosApiTransportError(f"Token refresh failed: {exc}", cause=exc) from exc

    def _ensure_token_sync(self) -> OAuth2Token:
        with self._sync_lock:
            tok = self._token
            if tok is not None and not tok.is_expired(skew_seconds=self._skew):
                return tok
            if (
                tok is not None
                and self._settings.normalized_refresh_url is not None
                and not tok.is_refresh_expired(skew_seconds=self._skew)
            ):
                self._token = self._refresh_token_sync(tok)
            else:
                self._token = self._fetch_token_sync()
            return self._token

    async def _fetch_token_async(self) -> OAuth2Token:
        try:
            token_dict = await self._oauth_async.fetch_token(
                url=self._settings.normalized_token_url,
                username=self._settings.username,
                password=self._settings.password,
                scope=self._settings.scope,
            )
            return OAuth2Token.from_authlib(token_dict)
        except _TOKEN_TRANSPORT_EXCEPTIONS as exc:
            raise PosApiTransportError(f"Token fetch failed: {exc}", cause=exc) from exc

    async def _refresh_token_async(self, current_token: OAuth2Token) -> OAuth2Token:
        try:
            token_dict = await self._oauth_async.refresh_token(
                url=self._settings.normalized_refresh_url,
                refresh_token=current_token.refresh_token,
            )
            return OAuth2Token.from_authlib(token_dict)
        except _TOKEN_TRANSPORT_EXCEPTIONS as exc:
            raise PosApiTransportError(f"Token refresh failed: {exc}", cause=exc) from exc

    async def _ensure_token_async(self) -> OAuth2Token:
        async with self._async_lock:
            tok = self._token
            if tok is not None and not tok.is_expired(skew_seconds=self._skew):
                return tok
            if (
                tok is not None
                and self._settings.normalized_refresh_url is not None
                and not tok.is_refresh_expired(skew_seconds=self._skew)
            ):
                self._token = await self._refresh_token_async(tok)
            else:
                self._token = await self._fetch_token_async()
            return self._token

    def _renew_after_401_sync(self, rejected: OAuth2Token) -> OAuth2Token:
        """Obtain a new token after the server rejected ``rejected`` with 401.

        If another thread already replaced the token, reuse theirs. Otherwise
        try the refresh grant when one is available and fall back to a full
        password grant if the refresh is itself rejected (a revoked session
        typically invalidates both tokens).
        """
        with self._sync_lock:
            current = self._token
            if current is not None and current is not rejected:
                return current
            new_token: OAuth2Token | None = None
            if (
                self._settings.normalized_refresh_url is not None
                and not rejected.is_refresh_expired(skew_seconds=self._skew)
            ):
                try:
                    new_token = self._refresh_token_sync(rejected)
                except PosApiTransportError:
                    new_token = None
            if new_token is None:
                new_token = self._fetch_token_sync()
            self._token = new_token
            return new_token

    async def _renew_after_401_async(self, rejected: OAuth2Token) -> OAuth2Token:
        """Async twin of :meth:`_renew_after_401_sync`."""
        async with self._async_lock:
            current = self._token
            if current is not None and current is not rejected:
                return current
            new_token: OAuth2Token | None = None
            if (
                self._settings.normalized_refresh_url is not None
                and not rejected.is_refresh_expired(skew_seconds=self._skew)
            ):
                try:
                    new_token = await self._refresh_token_async(rejected)
                except PosApiTransportError:
                    new_token = None
            if new_token is None:
                new_token = await self._fetch_token_async()
            self._token = new_token
            return new_token

    @staticmethod
    def _apply(request: httpx.Request, tok: OAuth2Token) -> None:
        request.headers["Authorization"] = f"{tok.token_type} {tok.access_token}"

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        try:
            tok = self._ensure_token_sync()
        except PosApiTransportError as exc:
            # The resource request has not been sent yet.
            exc.request = request
            exc.request_id = request.extensions.get("request_id")
            exc.request_sent = False
            raise
        self._apply(request, tok)
        response = yield request
        if response.status_code != httpx.codes.UNAUTHORIZED:
            return
        # One transparent renew-and-retry; a second 401 surfaces to the caller.
        tok = self._renew_after_401_sync(tok)
        self._apply(request, tok)
        yield request

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        try:
            tok = await self._ensure_token_async()
        except PosApiTransportError as exc:
            # The resource request has not been sent yet.
            exc.request = request
            exc.request_id = request.extensions.get("request_id")
            exc.request_sent = False
            raise
        self._apply(request, tok)
        response = yield request
        if response.status_code != httpx.codes.UNAUTHORIZED:
            return
        tok = await self._renew_after_401_async(tok)
        self._apply(request, tok)
        yield request
