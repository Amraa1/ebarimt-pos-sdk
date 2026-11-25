from __future__ import annotations

from typing import Any

import httpx

from ....auth import PasswordGrantAuth
from ....errors import PosApiBusinessError, PosApiConfigurationError
from ....settings import ApiClientSettings
from ....transport import AsyncTransport, SyncTransport
from ...base_resource import BaseResource, HeaderTypes
from .schema import CreateMerchantRegistrationRequest, CreateMerchantRegistrationResponse


class MerchantRegistrationResource(BaseResource):
    """Merchant registration: an operator asks eBarimt to add merchants to its POS.

    ``create`` only *submits* the request. eBarimt approves it later; poll
    ``EbarimtRestClient.info.read()`` until the merchant's TIN appears among the
    POS's merchants. There is no endpoint to query a registration's status.

    This is the only API-client resource that needs credentials: an OAuth2
    password-grant token and an ``X-API-KEY`` (``ApiClientSettings.api_key``).
    """

    def __init__(
        self,
        *,
        sync: SyncTransport,
        async_: AsyncTransport,
        settings: ApiClientSettings,
        token_auth: PasswordGrantAuth | None,
    ) -> None:
        super().__init__(sync=sync, async_=async_)
        self._settings = settings
        self._token_auth = token_auth

    @property
    def _path(self) -> str:
        return "/api/tpi/receipt/saveOprMerchants"

    def _ensure_business_success(self, data: Any, response: httpx.Response) -> None:
        """Raise ``PosApiBusinessError`` when a 2xx body's numeric ``status`` is not 200.

        This endpoint reports its result as ``{"msg", "status": 200, "code",
        "data"}``. A refusal is surfaced with eBarimt's ``msg`` and ``code``
        untouched; the SDK does not interpret them (an "already registered"
        refusal is the caller's to recognise).
        """
        if not isinstance(data, dict):
            return
        status = data.get("status")
        if not isinstance(status, int) or isinstance(status, bool) or status == 200:
            return
        message = data.get("msg")
        raise PosApiBusinessError(
            str(message) if message else f"Server returned status {status!r}",
            status=status,
            code=data.get("code"),
            request=response.request,
            response=response,
        )

    def _credentials(self, headers: HeaderTypes | None) -> tuple[PasswordGrantAuth, httpx.Headers]:
        """Return the token auth and the headers with ``X-API-KEY``, or raise
        ``PosApiConfigurationError`` naming every missing field. Runs before
        anything is sent."""
        api_key = self._settings.api_key
        missing = list(self._settings.missing_password_grant_fields)
        if api_key is None:
            missing.append("api_key")
        if missing or api_key is None or self._token_auth is None:
            raise PosApiConfigurationError(
                "merchant_registration requires token_url, client_id, username, "
                f"password and api_key in ApiClientSettings; missing: {', '.join(missing)}"
            )
        merged = httpx.Headers(headers)
        merged["X-API-KEY"] = api_key
        return self._token_auth, merged

    def create(
        self,
        payload: CreateMerchantRegistrationRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateMerchantRegistrationResponse:
        """Submit a merchant registration request. Approval is asynchronous."""
        auth, merged = self._credentials(headers)
        return self._send_sync_request(
            "POST",
            payload_model=CreateMerchantRegistrationRequest,
            payload=payload,
            response_model=CreateMerchantRegistrationResponse,
            headers=merged,
            auth=auth,
        )

    async def acreate(
        self,
        payload: CreateMerchantRegistrationRequest | dict[str, Any],
        *,
        headers: HeaderTypes | None = None,
    ) -> CreateMerchantRegistrationResponse:
        """Async twin of :meth:`create`."""
        auth, merged = self._credentials(headers)
        return await self._send_async_request(
            "POST",
            payload_model=CreateMerchantRegistrationRequest,
            payload=payload,
            response_model=CreateMerchantRegistrationResponse,
            headers=merged,
            auth=auth,
        )
