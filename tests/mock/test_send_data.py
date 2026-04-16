import httpx
import pytest
import respx

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

from ..helpers import BASE_REST_URL


@respx.mock
def test_send_data_ok_sync():
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/sendData").mock(
        return_value=httpx.Response(status_code=200)
    )

    with EbarimtRestClient(settings) as client:
        client.send_data.send()
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_send_data_ok_async():
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/sendData").mock(
        return_value=httpx.Response(status_code=200)
    )

    async with EbarimtRestClient(settings) as client:
        await client.send_data.asend()
        assert route.called
