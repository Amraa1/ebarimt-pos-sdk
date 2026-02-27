import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OAuth2Token:
    """
    Represents an OAuth2 access token response.

    Compatible with Keycloak / OpenID Connect token responses.

    Attributes:
        access_token: Bearer access token.
        token_type: Token type (usually 'Bearer').
        expires_in: Seconds until access token expires.
        refresh_token: Optional refresh token.
        refresh_expires_in: Seconds until refresh token expires.
        scope: Granted scope string.
        expires_at: Absolute UNIX timestamp when access token expires.
        raw: Original token response for advanced usage.
    """

    access_token: str
    token_type: str
    expires_in: int
    expires_at: int

    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    scope: str | None = None
    not_before_policy: int | None = None
    session_state: str | None = None

    raw: Mapping[str, Any] | None = None

    def is_expired(self, *, skew_seconds: float = 30) -> bool:
        """
        Returns True if access token is expired or about to expire.
        """
        return time.time() >= (self.expires_at - skew_seconds)

    def is_refresh_expired(self, *, skew_seconds: float = 30) -> bool:
        """
        Returns True if refresh token is expired.
        """
        if self.refresh_token is None or self.refresh_expires_in is None:
            return True

        refresh_expires_at = self.expires_at - self.expires_in + self.refresh_expires_in

        return time.time() >= (refresh_expires_at - skew_seconds)

    @classmethod
    def from_authlib(cls, token: Mapping[str, Any]) -> "OAuth2Token":
        return cls(
            access_token=token["access_token"],
            token_type=token.get("token_type", "Bearer"),
            expires_in=int(token.get("expires_in", 0)),
            expires_at=int(token["expires_at"]),
            not_before_policy=token.get("not-before-policy"),
            session_state=token.get("session_state"),
            refresh_token=token.get("refresh_token"),
            refresh_expires_in=(
                int(token["refresh_expires_in"])
                if token.get("refresh_expires_in") is not None
                else None
            ),
            scope=token.get("scope"),
            raw=token,
        )
