from __future__ import annotations

from dataclasses import dataclass

from .base_settings import BaseSettings


@dataclass(frozen=True, kw_only=True)
class ApiClientSettings(BaseSettings):
    """Settings for API client."""

    token_url: str
    refresh_url: str | None = None
    client_id: str
    client_secret: str | None = None  # Allowing client secret for future updates
    username: str
    password: str
    scope: str | None = None
    skew_seconds: float = 30

    @property
    def normalized_token_url(self) -> str:
        return self.token_url.strip()

    @property
    def normalized_refresh_url(self) -> str | None:
        return self.refresh_url.strip() if self.refresh_url else None
