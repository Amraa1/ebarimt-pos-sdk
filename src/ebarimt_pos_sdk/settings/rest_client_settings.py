from __future__ import annotations

from dataclasses import dataclass

from .base_settings import BaseSettings


@dataclass(frozen=True, kw_only=True)
class RestClientSettings(BaseSettings):
    """
    Settings for REST client.
    """

    pass
