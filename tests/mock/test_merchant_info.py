from datetime import date

import httpx
import pytest
import respx

from ebarimt_pos_sdk import ApiClientSettings, EbarimtApiClient

from ..data.merchant_info import SUCCESS_RESPONSE
from ..helpers import BASE_API_URL


def _settings() -> ApiClientSettings:
    # Public ebarimt info endpoints don't require OAuth2; credentials omitted.
    return ApiClientSettings(base_url=BASE_API_URL)


@respx.mock
def test_merchant_info_sync_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/info/check/getInfo").mock(
        return_value=httpx.Response(status_code=200, json=SUCCESS_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.merchant_info.read("01234567891")
        assert resp.data.name == "Test"
        assert resp.data.vatpayer_registered_date == date(2002, 4, 9)
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_merchant_info_async_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/info/check/getInfo").mock(
        return_value=httpx.Response(status_code=200, json=SUCCESS_RESPONSE)
    )
    async with EbarimtApiClient(settings=_settings()) as client:
        resp = await client.merchant_info.aread("01234567891")
        assert resp.data.name == "Test"
        assert resp.data.vatpayer_registered_date == date(2002, 4, 9)
        assert route.called
