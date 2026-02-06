from __future__ import annotations

from dataclasses import dataclass

from .transport import HeaderTypes


@dataclass(frozen=True)
class PosApiSettings:
    """
    SDK runtime settings.

    Notes:
        POS API usually runs on localhost or private network.
        `base_url` may be http://localhost:7080 or an internal hostname behind VPN.
    """

    base_url: str = "http://localhost:7080"
    timeout_s: float = 10.0
    verify_tls: bool = True

    # auth is intentionally flexible until spec is clearer:
    # e.g. {"Authorization": "Bearer ..."} or {"X-API-KEY": "..."}
    default_headers: HeaderTypes | None = None

    @property
    def normalized_base_url(self) -> str:
        """Normalizes base_url for clients to use.

        Returns:
            str: Normalized base_url.
        """
        return self.base_url.strip().rstrip("/")
