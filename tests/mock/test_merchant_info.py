from ..data.merchant_info import SUCCESS_RESPONSE
from ..data.auth import SUCCESS_RESPONSE as AUTH_SUCCESS_RESPONSE
from ..helpers import TOKEN_URL, CLIENT_ID, PASSWORD, USERNAME, BASE_API_URL
import respx
import httpx
from ebarimt_pos_sdk import ApiClientSettings, EbarimtApiClient
from datetime import date

@respx.mock    
def test_merchant_info_sync_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/info/check/getInfo").mock(return_value=httpx.Response(
        status_code=200,
        json=SUCCESS_RESPONSE,
    ))
    token_route = route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(
        status_code=200,
        json=AUTH_SUCCESS_RESPONSE,
    ))
    
    settings = ApiClientSettings(
        base_url=BASE_API_URL,
        token_url=TOKEN_URL,
        client_id=CLIENT_ID,
        username=USERNAME,
        password=PASSWORD
    )
    with EbarimtApiClient(settings=settings) as client:
    
        resp = client.merchant_info.read("01234567891")
        assert resp.data.name == "Test"
        assert resp.data.vatpayer_registered_date == date(2002, 4, 9)
        assert route.called
        assert token_route.called