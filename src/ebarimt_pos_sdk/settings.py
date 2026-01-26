from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass(frozen=True)
class PosApiSettings:
    """
    SDK runtime settings.

    Notes:
        POS API usually runs on localhost or private network. base_url should not end with slash.
    """

    base_url: str = "http://localhost:7080"
    timeout_s: float = 10.0
    verify_tls: bool = True

    # auth is intentionally flexible until spec is clearer:
    # e.g. {"Authorization": "Bearer ..."} or {"X-API-KEY": "..."}
    default_headers: Optional[Mapping[str, str]] = None

    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")
