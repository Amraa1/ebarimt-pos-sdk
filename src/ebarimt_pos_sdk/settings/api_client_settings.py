from __future__ import annotations

from dataclasses import dataclass

from .base_settings import BaseSettings


@dataclass(frozen=True, kw_only=True)
class ApiClientSettings(BaseSettings):
    """Settings for API client.

    The public ebarimt info endpoints (district codes, TIN info, merchant
    info, product tax codes, BÜNA classification) do not require auth, so
    every credential field below is optional. They remain for forward
    compatibility with endpoints that may require OAuth2 in the future.
    """

    token_url: str | None = None
    refresh_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    username: str | None = None
    password: str | None = None
    scope: str | None = None
    skew_seconds: float = 30

    def __post_init__(self) -> None:
        # Only validate fields when supplied — empty / whitespace strings are
        # always a misconfiguration regardless of whether auth is in use.
        for field_name in ("token_url", "client_id", "username", "password"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"ApiClientSettings.{field_name} cannot be empty or whitespace")

    @property
    def normalized_token_url(self) -> str | None:
        return self.token_url.strip() if self.token_url else None

    @property
    def normalized_refresh_url(self) -> str | None:
        return self.refresh_url.strip() if self.refresh_url else None
