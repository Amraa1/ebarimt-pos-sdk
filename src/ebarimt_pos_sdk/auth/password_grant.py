from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncGenerator, Generator

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client, OAuth2Client

from ..settings import ApiClientSettings
from .token import OAuth2Token


class PasswordGrantAuth(httpx.Auth):
    """
    OAuth2 Password Grant auth for httpx.Client and httpx.AsyncClient.

    Constraints:
      - Uses the same httpx clients owned by ApiClient (no extra clients).
      - Token calls bypass auth via `auth=None` to avoid recursion.
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

    # -------------------------
    # Token fetch/refresh (SYNC)
    # -------------------------

    def _fetch_token_sync(self) -> OAuth2Token:
        oauth = OAuth2Client(
            client_id=self._settings.client_id,
            client_secret=self._settings.client_secret,
            client=self._sync_http,
        )
        token_dict = oauth.fetch_token(
            url=self._settings.token_url,
            username=self._settings.username,
            password=self._settings.password,
            scope=getattr(self._settings, "scope", None),
            auth=None,  # ✅ critical: bypass this auth hook for token request
        )
        return OAuth2Token.from_authlib(token_dict)

    def _refresh_token_sync(self, refresh_token: str) -> OAuth2Token:
        oauth = OAuth2Client(
            client_id=self._settings.client_id,
            client_secret=self._settings.client_secret,
            client=self._sync_http,
        )
        token_dict = oauth.refresh_token(
            url=self._settings.token_url,
            refresh_token=refresh_token,
            auth=None,  # ✅ bypass auth hook
        )
        return OAuth2Token.from_authlib(token_dict)

    def _ensure_token_sync(self) -> OAuth2Token:
        tok = self._token
        if tok is not None and not tok.is_expired(skew_seconds=self._skew):
            return tok

        with self._sync_lock:
            tok = self._token
            if tok is not None and not tok.is_expired(skew_seconds=self._skew):
                return tok

            if (
                tok is not None
                and tok.refresh_token
                and not tok.is_refresh_expired(skew_seconds=self._skew)
            ):
                try:
                    self._token = self._refresh_token_sync(tok.refresh_token)
                    return self._token
                except Exception:
                    pass

            self._token = self._fetch_token_sync()
            return self._token

    # -------------------------
    # Token fetch/refresh (ASYNC)
    # -------------------------

    async def _fetch_token_async(self) -> OAuth2Token:
        oauth = AsyncOAuth2Client(
            client_id=self._settings.client_id,
            client_secret=self._settings.client_secret,
            client=self._async_http,
        )
        token_dict = await oauth.fetch_token(
            url=self._settings.token_url,
            username=self._settings.username,
            password=self._settings.password,
            scope=getattr(self._settings, "scope", None),
            auth=None,  # ✅ bypass auth hook
        )
        return OAuth2Token.from_authlib(token_dict)

    async def _refresh_token_async(self, refresh_token: str) -> OAuth2Token:
        oauth = AsyncOAuth2Client(
            client_id=self._settings.client_id,
            client_secret=self._settings.client_secret,
            client=self._async_http,
        )
        token_dict = await oauth.refresh_token(
            url=self._settings.token_url,
            refresh_token=refresh_token,
            auth=None,  # ✅ bypass auth hook
        )
        return OAuth2Token.from_authlib(token_dict)

    async def _ensure_token_async(self) -> OAuth2Token:
        tok = self._token
        if tok is not None and not tok.is_expired(skew_seconds=self._skew):
            return tok

        async with self._async_lock:
            tok = self._token
            if tok is not None and not tok.is_expired(skew_seconds=self._skew):
                return tok

            if (
                tok is not None
                and tok.refresh_token
                and not tok.is_refresh_expired(skew_seconds=self._skew)
            ):
                try:
                    self._token = await self._refresh_token_async(tok.refresh_token)
                    return self._token
                except Exception:
                    pass

            self._token = await self._fetch_token_async()
            return self._token

    # -------------------------
    # httpx.Auth hooks (correct typing)
    # -------------------------

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        tok = self._ensure_token_sync()
        request.headers["Authorization"] = f"{tok.token_type} {tok.access_token}"
        yield request

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        tok = await self._ensure_token_async()
        request.headers["Authorization"] = f"{tok.token_type} {tok.access_token}"
        yield request
