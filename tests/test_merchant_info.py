from .data.merchant_info import SUCCESS_RESPONSE
from .data.auth import SUCCESS_RESPONSE as AUTH_SUCCESS_RESPONSE
from .helpers import TOKEN_URL, CLIENT_ID, PASSWORD, USERNAME, BASE_API_URL
import respx
import httpx
from ebarimt_pos_sdk import api_settings_for_env, Environment, EbarimtApiClient
from datetime import date

msg = "Missing env vars"

return_value_success = httpx.Response(
    status_code=200,
    json=SUCCESS_RESPONSE,
)

@respx.mock    
def test_merchant_info_sync_ok() -> None:
    if TOKEN_URL is None:
        raise Exception(msg)
    if CLIENT_ID is None:
        raise Exception(msg)
    if USERNAME is None:
        raise Exception(msg)
    if PASSWORD is None:
        raise Exception(msg)
    if BASE_API_URL is None:
        raise Exception(msg)
    
    route = respx.get(f"{BASE_API_URL}/api/info/check/getInfo").mock(return_value=return_value_success)
    token_route = route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(
        status_code=200,
        json=AUTH_SUCCESS_RESPONSE,
    ))
    
    settings = api_settings_for_env(
        Environment.STAGING, 
        client_id=CLIENT_ID, 
        username=USERNAME, 
        password=PASSWORD,
        )
    with EbarimtApiClient(settings=settings) as client:
    
        resp = client.merchant_info.read("01234567891")
        assert resp.data.name == "Test"
        assert resp.data.vatpayer_registered_date == date(2002, 4, 9)
        assert route.called
        assert token_route.called