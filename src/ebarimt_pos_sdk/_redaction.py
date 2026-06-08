"""Redaction primitives shared by error formatting and logging.

Leaf module — depends only on the standard library and httpx so it can be
imported from both ``errors`` and ``_logging`` without creating a cycle.

Redaction is *allowlist-by-name*: query parameters and headers whose name is in
the sensitive sets are masked. Path segments are intentionally left intact —
the SDK only ever puts non-secret identifiers (e.g. TINs, BÜNA codes) in the
path, and TINs are public business identifiers.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
    }
)
SENSITIVE_QUERY_PARAMS = frozenset(
    {
        "access_token",
        "refresh_token",
        "token",
        "id_token",
        "code",
        "client_secret",
    }
)

_MASK = "***"


def redact_url(url: httpx.URL) -> str:
    """Return ``url`` as a string with token-bearing query params and any
    fragment stripped. Path segments are left untouched."""
    parts = urlsplit(str(url))
    if not parts.query and not parts.fragment:
        return str(url)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    redacted = [(k, _MASK if k.lower() in SENSITIVE_QUERY_PARAMS else v) for k, v in pairs]
    # safe="*" keeps the mask readable as `***` rather than `%2A%2A%2A`.
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(redacted, safe="*"), ""))


def redact_headers(headers: httpx.Headers) -> dict[str, str]:
    """Return a plain dict of headers with sensitive values masked by name."""
    return {k: _MASK if k.lower() in SENSITIVE_HEADERS else v for k, v in headers.items()}
