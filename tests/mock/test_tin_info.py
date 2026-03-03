from ..data.tin_info import SUCCESS_RESPONSE
from ..data.auth import SUCCESS_RESPONSE as AUTH_SUCCESS_RESPONSE
from ..helpers import TOKEN_URL, CLIENT_ID, PASSWORD, USERNAME, BASE_API_URL
import respx
import httpx
from ebarimt_pos_sdk import api_settings_for_env, Environment, EbarimtApiClient


@respx.mock
def test_tin_info_sync_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/info/check/getTinInfo").mock(return_value=httpx.Response(
        status_code=200,
        json=SUCCESS_RESPONSE,
    ))
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
        resp = client.tin_info.read("5051045")
        assert resp.data == "16000859970"
        assert route.called
        assert token_route.called
        
        