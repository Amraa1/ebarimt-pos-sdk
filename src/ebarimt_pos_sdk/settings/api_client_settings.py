from __future__ import annotations

from dataclasses import dataclass, field

from .base_settings import BaseSettings


@dataclass(frozen=True, kw_only=True)
class ApiClientSettings(BaseSettings):
    """Settings for API client.

    The public ebarimt info endpoints (district codes, TIN info, merchant
    info, product tax codes, BÜNA classification) do not require auth, so
    every credential field below is optional, and the client never sends a
    token or API key to those endpoints.

    The credentials are used only by ``merchant_registration``
    (``saveOprMerchants``), which needs an OAuth2 password-grant token
    (``token_url``, ``client_id``, ``username``, ``password``; ``client_secret``
    and ``scope`` when the realm requires them) and an ``api_key`` sent as
    ``X-API-KEY``.
    """

    token_url: str | None = None
    refresh_url: str | None = None
    client_id: str | None = None
    # Secrets are excluded from ``repr()`` so a settings object that ends up in
    # a log line, traceback, or debugger dump never prints credentials.
    client_secret: str | None = field(default=None, repr=False)
    username: str | None = None
    password: str | None = field(default=None, repr=False)
    scope: str | None = None
    # ``X-API-KEY`` for ``saveOprMerchants``; a secret, so excluded from repr().
    api_key: str | None = field(default=None, repr=False)
    skew_seconds: float = 30

    def __post_init__(self) -> None:
        # Only validate fields when supplied — empty / whitespace strings are
        # always a misconfiguration regardless of whether auth is in use.
        for field_name in ("token_url", "client_id", "username", "password", "api_key"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"ApiClientSettings.{field_name} cannot be empty or whitespace")

    @property
    def has_password_grant_credentials(self) -> bool:
        """True when every field a password-grant token request needs is set."""
        return not self.missing_password_grant_fields

    @property
    def missing_password_grant_fields(self) -> tuple[str, ...]:
        """Names of the required password-grant fields that are not set."""
        return tuple(
            name
            for name in ("token_url", "client_id", "username", "password")
            if getattr(self, name) is None
        )

    @property
    def normalized_token_url(self) -> str | None:
        return self.token_url.strip() if self.token_url else None

    @property
    def normalized_refresh_url(self) -> str | None:
        return self.refresh_url.strip() if self.refresh_url else None
