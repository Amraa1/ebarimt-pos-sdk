from __future__ import annotations

from dataclasses import dataclass, field

_DEFAULT_RETRYABLE_STATUSES: frozenset[int] = frozenset({500, 502, 503, 504})


@dataclass(frozen=True, kw_only=True)
class RetrySettings:
    """Configuration for transport retry behaviour."""

    max_retries: int = 3
    retryable_statuses: frozenset[int] = field(default_factory=lambda: _DEFAULT_RETRYABLE_STATUSES)
    backoff_base_seconds: float = 1.0

    def __post_init__(self) -> None:
        if self.max_retries < 1:
            raise ValueError("RetrySettings.max_retries must be >= 1")
        if self.backoff_base_seconds < 0:
            raise ValueError("RetrySettings.backoff_base_seconds must be >= 0")

    def sleep_seconds(self, attempt: int) -> float:
        """Return the sleep duration before the next retry (exponential backoff)."""
        return float(self.backoff_base_seconds * (2**attempt))
