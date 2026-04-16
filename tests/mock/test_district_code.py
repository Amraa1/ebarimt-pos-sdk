import httpx
import pytest
import respx

from ebarimt_pos_sdk import ApiClientSettings, EbarimtApiClient

from ..data.auth import SUCCESS_RESPONSE as AUTH_SUCCESS_RESPONSE
from ..data.district_code import SUCCESS_RESPONSE
from ..helpers import BASE_API_URL, CLIENT_ID, PASSWORD, TOKEN_URL, USERNAME


def _settings() -> ApiClientSettings:
    return ApiClientSettings(
        base_url=BASE_API_URL,
        token_url=TOKEN_URL,
        client_id=CLIENT_ID,
        username=USERNAME,
        password=PASSWORD,
    )


@respx.mock
def test_district_code_sync_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/info/check/getBranchInfo").mock(
        return_value=httpx.Response(status_code=200, json=SUCCESS_RESPONSE)
    )
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(status_code=200, json=AUTH_SUCCESS_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.district_code.read()
        assert len(resp.data) > 0
        assert route.called
        assert token_route.called


@pytest.mark.asyncio
@respx.mock
async def test_district_code_async_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/info/check/getBranchInfo").mock(
        return_value=httpx.Response(status_code=200, json=SUCCESS_RESPONSE)
    )
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(status_code=200, json=AUTH_SUCCESS_RESPONSE)
    )
    async with EbarimtApiClient(settings=_settings()) as client:
        resp = await client.district_code.aread()
        assert len(resp.data) > 0
        assert route.called
        assert token_route.called
