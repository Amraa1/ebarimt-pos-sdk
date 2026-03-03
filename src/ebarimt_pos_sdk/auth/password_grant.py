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
        self._oauth_sync = OAuth2Client(
            client_id=self._settings.client_id,
            client_secret=self._settings.client_secret,
            client=self._sync_http,
        )
        self._oauth_async = AsyncOAuth2Client(
            client_id=self._settings.client_id,
            client_secret=self._settings.client_secret,
            client=self._async_http,
        )

    def _fetch_token_sync(self) -> OAuth2Token:
        token_dict = self._oauth_sync.fetch_token(
            url=self._settings.token_url,
            username=self._settings.username,
            password=self._settings.password,
            scope=getattr(self._settings, "scope", None),
            auth=None,
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

            self._token = self._fetch_token_sync()
            return self._token

    async def _fetch_token_async(self) -> OAuth2Token:
        token_dict = await self._oauth_async.fetch_token(
            url=self._settings.token_url,
            username=self._settings.username,
            password=self._settings.password,
            scope=getattr(self._settings, "scope", None),
            auth=None,
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

            self._token = await self._fetch_token_async()
            return self._token

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
