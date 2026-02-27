from __future__ import annotations

from dataclasses import dataclass

from .._types import HeaderTypes


@dataclass(frozen=True)
class BaseSettings:
    """
    Base settings class for Ebarimt SDK clients.
    """

    base_url: str

    timeout_s: float = 10.0
    verify_tls: bool = True

    headers: HeaderTypes | None = None

    @property
    def normalized_base_url(self) -> str:
        """Normalizes base_url for clients to use.

        Returns:
            str: Normalized base_url.
        """
        return self.base_url.strip().rstrip("/")
