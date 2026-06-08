"""
Ebarimt api settings factory
"""

from dataclasses import dataclass
from enum import Enum, auto

from .settings import ApiClientSettings


class Environment(Enum):
    PRODUCTION = auto()
    STAGING = auto()


@dataclass(frozen=True, slots=True)
class _ApiPreset:
    base_url: str
    token_url: str
    refresh_url: str | None = None


_PRESETS: dict[Environment, _ApiPreset] = {
    Environment.STAGING: _ApiPreset(
        base_url="https://st-api.ebarimt.mn",
        token_url="https://st.auth.itc.gov.mn/auth/realms/Staging/protocol/openid-connect/token",
    ),
    Environment.PRODUCTION: _ApiPreset(
        base_url="https://api.ebarimt.mn",
        token_url="https://auth.itc.gov.mn/auth/realms/ITC/protocol/openid-connect/token",
    ),
}


def create_api_settings(
    env: Environment,
    *,
    client_id: str | None = None,
    username: str | None = None,
    password: str | None = None,
    client_secret: str | None = None,
    scope: str | None = None,
    timeout_s: float = 10.0,
    verify_tls: bool = True,
    skew_seconds: float = 30,
) -> ApiClientSettings:
    """Ebarimt api settings factory.

    The public ebarimt info endpoints don't require OAuth2, so credentials
    are optional. They are preserved for forward-compat with any endpoint
    that may later require token auth.
    """

    p = _PRESETS[env]
    return ApiClientSettings(
        base_url=p.base_url,
        token_url=p.token_url,
        refresh_url=p.refresh_url,
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        scope=scope,
        timeout_s=timeout_s,
        verify_tls=verify_tls,
        skew_seconds=skew_seconds,
    )
