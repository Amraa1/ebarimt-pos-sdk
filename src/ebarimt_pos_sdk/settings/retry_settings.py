from __future__ import annotations

from dataclasses import dataclass, field

_DEFAULT_RETRYABLE_STATUSES: frozenset[int] = frozenset({500, 502, 503, 504})

# Methods that are idempotent per RFC 9110 §9.2.2 and therefore safe to
# re-send automatically. POST and PATCH are deliberately absent: a receipt
# POST whose response was lost to a timeout may already have been persisted by
# PosAPI, and re-sending it would issue a duplicate е-баримт (#77).
_DEFAULT_RETRY_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})


@dataclass(frozen=True, kw_only=True)
class RetrySettings:
    """Configuration for transport retry behaviour.

    Retries apply only to requests whose HTTP method is in ``retry_methods``;
    any other method is sent exactly once regardless of ``max_retries``. Opt a
    non-idempotent method in explicitly if your deployment guarantees it is
    safe, e.g. ``retry_methods=RetrySettings.DEFAULT_RETRY_METHODS | {"POST"}``.
    """

    DEFAULT_RETRY_METHODS = _DEFAULT_RETRY_METHODS

    max_retries: int = 3
    retryable_statuses: frozenset[int] = field(default_factory=lambda: _DEFAULT_RETRYABLE_STATUSES)
    backoff_base_seconds: float = 1.0
    retry_methods: frozenset[str] = field(default_factory=lambda: _DEFAULT_RETRY_METHODS)

    def __post_init__(self) -> None:
        if self.max_retries < 1:
            raise ValueError("RetrySettings.max_retries must be >= 1")
        if self.backoff_base_seconds < 0:
            raise ValueError("RetrySettings.backoff_base_seconds must be >= 0")
        # Normalise so ``{"post"}`` and ``{"POST"}`` behave the same.
        object.__setattr__(self, "retry_methods", frozenset(m.upper() for m in self.retry_methods))

    def is_retryable_method(self, method: str) -> bool:
        """Return True if requests with this HTTP method may be re-sent."""
        return method.upper() in self.retry_methods

    def attempts_for(self, method: str) -> int:
        """Number of attempts the transport may make for ``method``: ``max_retries``
        for retryable methods, exactly 1 otherwise."""
        return self.max_retries if self.is_retryable_method(method) else 1

    def sleep_seconds(self, attempt: int) -> float:
        """Return the sleep duration before the next retry (exponential backoff)."""
        return float(self.backoff_base_seconds * (2**attempt))
