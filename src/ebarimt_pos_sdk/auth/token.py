import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar


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

    # Token material is excluded from ``repr()`` so an OAuth2Token that ends
    # up in a log line, traceback, or debugger dump never prints a bearer
    # token. ``raw`` is excluded for the same reason (it holds both tokens).
    access_token: str = field(repr=False)
    token_type: str
    expires_in: int
    expires_at: int

    refresh_token: str | None = field(default=None, repr=False)
    refresh_expires_in: int | None = None
    scope: str | None = None
    not_before_policy: int | None = None
    session_state: str | None = None

    raw: Mapping[str, Any] | None = field(default=None, repr=False)

    # Lifetime assumed when a token response omits ``expires_in`` (Keycloak's
    # default access-token lifespan).
    DEFAULT_EXPIRES_IN: ClassVar[int] = 300

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
        """Build a token from an OAuth2 token response.

        ``expires_at`` is taken from the response when present; otherwise it is
        derived from ``expires_in`` at the time of the call (a raw Keycloak
        response carries only ``expires_in``). ``expires_in`` is optional in
        RFC 6749; when it is absent the token is assumed to last
        ``DEFAULT_EXPIRES_IN`` seconds, so it is reused rather than refetched on
        every call (a server that revokes it earlier triggers the 401 renewal).
        """
        raw_expires_in = token.get("expires_in")
        expires_in = int(raw_expires_in) if raw_expires_in is not None else cls.DEFAULT_EXPIRES_IN
        expires_at = token.get("expires_at")
        return cls(
            access_token=token["access_token"],
            token_type=token.get("token_type", "Bearer"),
            expires_in=expires_in,
            expires_at=int(expires_at) if expires_at is not None else int(time.time()) + expires_in,
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
