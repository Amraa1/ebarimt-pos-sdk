"""Merchant registration (``saveOprMerchants``): the only API-client resource that
needs credentials — a password-grant bearer token and an ``X-API-KEY``."""

from __future__ import annotations

import httpx
import pytest
import respx

from ebarimt_pos_sdk import (
    ApiClientSettings,
    CreateMerchantRegistrationResponse,
    EbarimtApiClient,
    PosApiBusinessError,
    PosApiConfigurationError,
    PosApiError,
    PosApiHttpError,
    PosApiTransportError,
    PosApiValidationError,
)
from ebarimt_pos_sdk.settings import RetrySettings

from ..data.merchant_registration import (
    HTTP_ERROR_RESPONSE,
    REFUSAL_IN_200_RESPONSE,
    REQUEST_PAYLOAD,
    SUCCESS_RESPONSE,
    TOKEN_RESPONSE,
)

BASE_URL = "https://api.example.mn"
TOKEN_URL = "https://auth.example.mn/token"
ENDPOINT = f"{BASE_URL}/api/tpi/receipt/saveOprMerchants"
API_KEY = "test-api-key-123"


def make_settings(**overrides: object) -> ApiClientSettings:
    fields: dict[str, object] = {
        "base_url": BASE_URL,
        "token_url": TOKEN_URL,
        "client_id": "cid",
        "username": "operator",
        "password": "s3cret",
        "api_key": API_KEY,
    }
    fields.update(overrides)
    return ApiClientSettings(**fields)  # type: ignore[arg-type]


@respx.mock
def test_create_sends_bearer_token_and_api_key() -> None:
    token_route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=SUCCESS_RESPONSE))

    with EbarimtApiClient(make_settings()) as client:
        result = client.merchant_registration.create(REQUEST_PAYLOAD)

    assert isinstance(result, CreateMerchantRegistrationResponse)
    assert result.status == 200
    assert result.msg == SUCCESS_RESPONSE["msg"]
    assert token_route.call_count == 1
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer ACCESS-TOKEN-1"
    assert sent.headers["X-API-KEY"] == API_KEY
    assert sent.read() == (b'{"posNo":"10005299","merchantTins":["77001059076","83000874855"]}')


def test_token_request_goes_through_the_clients_own_http_client() -> None:
    """The token request must use the SDK's HTTP client (and so its proxy, TLS,
    timeout and injected transport), not a separate default client."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if str(request.url) == TOKEN_URL:
            return httpx.Response(200, json=TOKEN_RESPONSE)
        return httpx.Response(200, json=SUCCESS_RESPONSE)

    injected = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler))
    with EbarimtApiClient(make_settings(client_secret="csecret"), sync_client=injected) as client:
        client.merchant_registration.create(REQUEST_PAYLOAD)

    assert [str(r.url) for r in seen] == [TOKEN_URL, ENDPOINT]
    token_request = seen[0]
    assert token_request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert "Authorization" not in token_request.headers
    form = dict(httpx.QueryParams(token_request.read().decode()))
    assert form == {
        "grant_type": "password",
        "username": "operator",
        "password": "s3cret",
        "client_id": "cid",
        "client_secret": "csecret",
    }


@pytest.mark.parametrize(
    ("overrides", "missing"),
    [
        ({"password": None, "api_key": None}, "password, api_key"),
        ({"api_key": None}, "api_key"),
        ({"token_url": None, "client_id": None}, "token_url, client_id"),
    ],
)
def test_create_without_credentials_raises_before_sending(
    overrides: dict[str, object], missing: str
) -> None:
    with respx.mock(assert_all_called=False) as router:
        token_route = router.post(TOKEN_URL)
        route = router.post(ENDPOINT)
        with EbarimtApiClient(make_settings(**overrides)) as client:
            with pytest.raises(PosApiConfigurationError) as excinfo:
                client.merchant_registration.create(REQUEST_PAYLOAD)

    error = excinfo.value
    assert isinstance(error, PosApiError)
    assert error.request_sent is False
    assert f"missing: {missing}" in error.message
    assert not token_route.called
    assert not route.called


@pytest.mark.asyncio
async def test_acreate_without_credentials_raises_before_sending() -> None:
    with respx.mock(assert_all_called=False) as router:
        route = router.post(ENDPOINT)
        async with EbarimtApiClient(ApiClientSettings(base_url=BASE_URL)) as client:
            with pytest.raises(PosApiConfigurationError) as excinfo:
                await client.merchant_registration.acreate(REQUEST_PAYLOAD)

    assert "missing: token_url, client_id, username, password, api_key" in excinfo.value.message
    assert not route.called


def test_public_resources_send_no_credentials_even_when_configured() -> None:
    from ..data.tin_info import SUCCESS_RESPONSE as TIN_SUCCESS

    with respx.mock(assert_all_called=False) as router:
        token_route = router.post(TOKEN_URL)
        route = router.get(f"{BASE_URL}/api/info/check/getTinInfo").mock(
            return_value=httpx.Response(200, json=TIN_SUCCESS)
        )
        with EbarimtApiClient(make_settings()) as client:
            client.tin_info.read("УБ12345678")

    sent = route.calls.last.request
    assert "Authorization" not in sent.headers
    assert "X-API-KEY" not in sent.headers
    assert not token_route.called


@respx.mock
def test_refusal_inside_a_200_raises_business_error() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=REFUSAL_IN_200_RESPONSE))

    with EbarimtApiClient(make_settings()) as client:
        with pytest.raises(PosApiBusinessError) as excinfo:
            client.merchant_registration.create(REQUEST_PAYLOAD)

    error = excinfo.value
    assert error.message == REFUSAL_IN_200_RESPONSE["msg"]
    assert error.status == 400
    assert error.code == "MERCHANT_ALREADY_REGISTERED"


@pytest.mark.asyncio
@respx.mock
async def test_http_error_keeps_ebarimt_msg() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
    respx.post(ENDPOINT).mock(return_value=httpx.Response(400, json=HTTP_ERROR_RESPONSE))

    async with EbarimtApiClient(make_settings()) as client:
        with pytest.raises(PosApiHttpError) as excinfo:
            await client.merchant_registration.acreate(REQUEST_PAYLOAD)

    assert f"Message: {HTTP_ERROR_RESPONSE['msg']}" in excinfo.value.message


@respx.mock
def test_timeout_after_sending_is_not_resent() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
    route = respx.post(ENDPOINT).mock(side_effect=httpx.ReadTimeout("read timed out"))
    settings = make_settings(retry=RetrySettings(max_retries=3, retry_unsent=True))

    with EbarimtApiClient(settings) as client:
        with pytest.raises(PosApiTransportError) as excinfo:
            client.merchant_registration.create(REQUEST_PAYLOAD)

    assert excinfo.value.request_sent is True
    assert route.call_count == 1


@respx.mock
def test_401_renews_the_token_and_resends_once() -> None:
    respx.post(TOKEN_URL).mock(
        side_effect=[
            httpx.Response(200, json=TOKEN_RESPONSE),
            httpx.Response(200, json={**TOKEN_RESPONSE, "access_token": "ACCESS-TOKEN-2"}),
        ]
    )
    route = respx.post(ENDPOINT).mock(
        side_effect=[httpx.Response(401), httpx.Response(200, json=SUCCESS_RESPONSE)]
    )

    with EbarimtApiClient(make_settings()) as client:
        result = client.merchant_registration.create(REQUEST_PAYLOAD)

    assert result.status == 200
    assert [c.request.headers["Authorization"] for c in route.calls] == [
        "Bearer ACCESS-TOKEN-1",
        "Bearer ACCESS-TOKEN-2",
    ]
    assert all(c.request.headers["X-API-KEY"] == API_KEY for c in route.calls)


@respx.mock
def test_token_is_fetched_once_and_reused() -> None:
    token_route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=SUCCESS_RESPONSE))

    with EbarimtApiClient(make_settings()) as client:
        client.merchant_registration.create(REQUEST_PAYLOAD)
        client.merchant_registration.create(REQUEST_PAYLOAD)

    assert token_route.call_count == 1


def test_api_key_is_hidden_from_settings_repr() -> None:
    from ebarimt_pos_sdk import Environment, create_api_settings

    settings = create_api_settings(Environment.STAGING, api_key=API_KEY, password="s3cret")

    assert settings.api_key == API_KEY
    assert API_KEY not in repr(settings)
    assert "s3cret" not in repr(settings)


@respx.mock
def test_secrets_stay_out_of_logs_and_error_strings(caplog: pytest.LogCaptureFixture) -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
    respx.post(ENDPOINT).mock(return_value=httpx.Response(400, json=HTTP_ERROR_RESPONSE))

    with caplog.at_level("DEBUG", logger="ebarimt_pos_sdk"):
        with EbarimtApiClient(make_settings()) as client:
            with pytest.raises(PosApiHttpError) as excinfo:
                client.merchant_registration.create(REQUEST_PAYLOAD)

    rendered = str(excinfo.value)
    assert "X-API-KEY" in rendered or "x-api-key" in rendered  # the header is listed...
    for secret in (API_KEY, "ACCESS-TOKEN-1", "s3cret"):
        assert secret not in rendered  # ...but its value is masked
        assert secret not in caplog.text


@pytest.mark.asyncio
@respx.mock
async def test_acreate_sends_bearer_token_and_api_key() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=SUCCESS_RESPONSE))

    async with EbarimtApiClient(make_settings()) as client:
        result = await client.merchant_registration.acreate(REQUEST_PAYLOAD)

    assert result.status == 200
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer ACCESS-TOKEN-1"
    assert sent.headers["X-API-KEY"] == API_KEY


@pytest.mark.parametrize(
    "payload",
    [
        {"pos_no": "10005299", "merchant_tins": ["1234"]},
        {"pos_no": "10005299", "merchant_tins": ["7700105907a"]},
        {"pos_no": "10005299", "merchant_tins": []},
        {"pos_no": "  ", "merchant_tins": ["77001059076"]},
    ],
)
def test_malformed_request_is_rejected_before_sending(payload: dict[str, object]) -> None:
    with respx.mock(assert_all_called=False) as router:
        token_route = router.post(TOKEN_URL)
        route = router.post(ENDPOINT)
        with EbarimtApiClient(make_settings()) as client:
            with pytest.raises(PosApiValidationError):
                client.merchant_registration.create(payload)

    assert not token_route.called
    assert not route.called


def test_rejected_login_surfaces_oauth_error_without_sending() -> None:
    with respx.mock(assert_all_called=False) as router:
        router.post(TOKEN_URL).mock(
            return_value=httpx.Response(
                401,
                json={"error": "invalid_grant", "error_description": "Invalid user credentials"},
            )
        )
        route = router.post(ENDPOINT)
        with EbarimtApiClient(make_settings()) as client:
            with pytest.raises(PosApiTransportError) as excinfo:
                client.merchant_registration.create(REQUEST_PAYLOAD)

    error = excinfo.value
    assert error.request_sent is False
    assert "invalid_grant (Invalid user credentials)" in error.message
    assert "s3cret" not in str(error)
    assert not route.called
