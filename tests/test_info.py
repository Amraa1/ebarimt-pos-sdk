import httpx
import pytest
import respx

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings
from .data.info import SUCCESS_RESPONSE
return_value_success = httpx.Response(
    200,
    json=SUCCESS_RESPONSE,
)



@pytest.mark.asyncio
@respx.mock
async def test_info_read_async_ok() -> None:
    base_url = "http://localhost:7080"
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(return_value=return_value_success)

    async with EbarimtRestClient(settings) as client:
        resp = await client.info.aread()
        assert resp.operator_name == "TEST OPERATOR 1"
        assert route.called


@respx.mock
def test_info_read_sync_ok() -> None:
    base_url = "http://localhost:7080"
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(return_value=return_value_success)

    with EbarimtRestClient(settings) as client:
        resp = client.info.read()
        assert resp.operator_name == "TEST OPERATOR 1"
        assert route.called
