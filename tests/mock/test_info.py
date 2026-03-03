import httpx
import pytest
import respx

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings
from ..data.info import SUCCESS_RESPONSE
from ..helpers import BASE_REST_URL


@pytest.mark.asyncio
@respx.mock
async def test_info_read_async_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(return_value=httpx.Response(
        200,
        json=SUCCESS_RESPONSE,
    ))

    async with EbarimtRestClient(settings) as client:
        resp = await client.info.aread()
        assert resp.operator_name == "TEST OPERATOR 1"
        assert route.called


@respx.mock
def test_info_read_sync_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(return_value=httpx.Response(
        200,
        json=SUCCESS_RESPONSE,
    ))

    with EbarimtRestClient(settings) as client:
        resp = client.info.read()
        assert resp.operator_name == "TEST OPERATOR 1"
        assert route.called
