import httpx
import pytest
import respx

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

from ..data.bank_accounts import SUCCESS_RESPONSE
from ..helpers import BASE_REST_URL, TIN


@respx.mock
def test_bank_accounts_read_sync_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url, headers=None)
    tin = TIN

    route = respx.get(f"{base_url}/rest/bankAccounts").mock(
        return_value=httpx.Response(200, json=SUCCESS_RESPONSE)
    )

    with EbarimtRestClient(settings) as client:
        resp = client.bank_accounts.read(tin=tin)
        assert resp[0].tin == tin
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_bank_accounts_read_async_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)
    tin = TIN

    route = respx.get(f"{base_url}/rest/bankAccounts").mock(
        return_value=httpx.Response(200, json=SUCCESS_RESPONSE)
    )

    with EbarimtRestClient(settings) as client:
        resp = await client.bank_accounts.aread(tin=tin)
        assert resp[0].tin == tin
        assert route.called
