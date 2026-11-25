"""Fixtures for ``POST /api/tpi/receipt/saveOprMerchants`` (merchant registration).

Only the success body is documented (spec/openapi/posapi-3.0.yaml). The PosAPI
3.0.1 user manual does not cover this call, so the refusal bodies below are
ASSUMED: they follow the documented ``{msg, status, code, data}`` envelope with a
non-200 ``status``. Replace them with captured staging responses when available.
"""

REQUEST_PAYLOAD = {
    "pos_no": "10005299",
    "merchant_tins": ["77001059076", "83000874855"],
}

SUCCESS_RESPONSE = {
    "msg": "Мерчант бүртгэх хүсэлт амжилттай илгээгдлээ.",
    "status": 200,
    "code": None,
    "data": None,
}

# ASSUMED shape: HTTP 200 carrying a refusal in the body.
REFUSAL_IN_200_RESPONSE = {
    "msg": "Мерчант бүртгэлтэй байна.",
    "status": 400,
    "code": "ASSUMED_CODE",  # placeholder, not an observed eBarimt code
    "data": None,
}

# ASSUMED shape: a non-2xx response using the same envelope (``msg``, not ``message``).
HTTP_ERROR_RESPONSE = {
    "msg": "Посын дугаар буруу байна.",
    "status": 400,
    "code": None,
    "data": None,
}

TOKEN_RESPONSE = {
    "access_token": "ACCESS-TOKEN-1",
    "token_type": "Bearer",
    "expires_in": 300,
}
