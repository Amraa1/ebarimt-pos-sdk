from __future__ import annotations

import random
from dataclasses import dataclass, field

# 429 is included: it is the most likely throttling response from the OAuth2
# endpoint and from PosAPI under load, and the server usually tells us how
# long to wait via ``Retry-After`` (see ``sleep_seconds``).
_DEFAULT_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})

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

    Backoff is exponential (``backoff_base_seconds * 2**attempt``) capped at
    ``max_backoff_seconds``, with *full jitter* (uniform in ``[0, backoff]``)
    when ``jitter`` is on, so a fleet of POS devices that fail together does
    not retry in lockstep. A ``Retry-After`` header from the server, when
    ``respect_retry_after`` is on, replaces the computed backoff (still capped).
    """

    DEFAULT_RETRY_METHODS = _DEFAULT_RETRY_METHODS

    max_retries: int = 3
    retryable_statuses: frozenset[int] = field(default_factory=lambda: _DEFAULT_RETRYABLE_STATUSES)
    backoff_base_seconds: float = 1.0
    max_backoff_seconds: float = 30.0
    jitter: bool = True
    respect_retry_after: bool = True
    retry_methods: frozenset[str] = field(default_factory=lambda: _DEFAULT_RETRY_METHODS)

    def __post_init__(self) -> None:
        if self.max_retries < 1:
            raise ValueError("RetrySettings.max_retries must be >= 1")
        if self.backoff_base_seconds < 0:
            raise ValueError("RetrySettings.backoff_base_seconds must be >= 0")
        if self.max_backoff_seconds < 0:
            raise ValueError("RetrySettings.max_backoff_seconds must be >= 0")
        # Normalise so ``{"post"}`` and ``{"POST"}`` behave the same.
        object.__setattr__(self, "retry_methods", frozenset(m.upper() for m in self.retry_methods))

    def is_retryable_method(self, method: str) -> bool:
        """Return True if requests with this HTTP method may be re-sent."""
        return method.upper() in self.retry_methods

    def attempts_for(self, method: str) -> int:
        """Number of attempts the transport may make for ``method``: ``max_retries``
        for retryable methods, exactly 1 otherwise."""
        return self.max_retries if self.is_retryable_method(method) else 1

    def sleep_seconds(self, attempt: int, *, retry_after: float | None = None) -> float:
        """Return the sleep duration before the next retry.

        ``attempt`` is the 0-based index of the attempt that just failed.
        ``retry_after`` is the server-requested delay in seconds (already
        parsed from a ``Retry-After`` header), or ``None`` if absent.
        """
        if retry_after is not None and self.respect_retry_after:
            # The server's own instruction wins over our schedule; it is not
            # jittered (the server has already spread clients out) but it is
            # capped so a hostile/buggy header cannot stall the client.
            return float(min(max(retry_after, 0.0), self.max_backoff_seconds))
        backoff = min(self.backoff_base_seconds * (2**attempt), self.max_backoff_seconds)
        if self.jitter and backoff > 0:
            return random.uniform(0.0, backoff)
        return float(backoff)
