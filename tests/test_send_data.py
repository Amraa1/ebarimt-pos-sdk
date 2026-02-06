import httpx
import pytest
import respx

from ebarimt_pos_sdk import PosApiClient, PosApiSettings


@respx.mock
def test_send_data_ok_sync():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/sendData").mock(
        return_value=httpx.Response(status_code=200)
    )

    with PosApiClient(settings) as client:
        client.send_data.send()
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_send_data_ok_async():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/sendData").mock(
        return_value=httpx.Response(status_code=200)
    )

    async with PosApiClient(settings) as client:
        await client.send_data.asend()
        assert route.called
