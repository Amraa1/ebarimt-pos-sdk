from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


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
    default_headers: Mapping[str, str] | None = None

    def normalized_base_url(self) -> str:
        # keep normalization in one place; client uses this
        return self.base_url.strip().rstrip("/")
