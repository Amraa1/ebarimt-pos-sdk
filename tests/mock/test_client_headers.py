import httpx
import pytest
import respx

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

from ..data.bank_accounts import SUCCESS_RESPONSE
from ..helpers import BASE_REST_URL, TIN


def _route() -> respx.Route:
    return respx.get(f"{BASE_REST_URL}/rest/bankAccounts").mock(
        return_value=httpx.Response(200, json=SUCCESS_RESPONSE)
    )


@respx.mock
def test_owned_client_sends_client_headers_sync() -> None:
    route = _route()
    settings = RestClientSettings(base_url=BASE_REST_URL)

    with EbarimtRestClient(settings, headers={"X-Api-Key": "k"}) as client:
        # Header set on the client becomes an httpx default header.
        assert client._sync_client.headers["x-api-key"] == "k"
        client.bank_accounts.read(tin=TIN)

    assert route.calls.last.request.headers["x-api-key"] == "k"


@pytest.mark.asyncio
@respx.mock
async def test_owned_client_sends_client_headers_async() -> None:
    route = _route()
    settings = RestClientSettings(base_url=BASE_REST_URL)

    async with EbarimtRestClient(settings, headers={"X-Api-Key": "k"}) as client:
        assert client._async_client.headers["x-api-key"] == "k"
        await client.bank_accounts.aread(tin=TIN)

    assert route.calls.last.request.headers["x-api-key"] == "k"


@respx.mock
def test_per_call_header_overrides_client_header() -> None:
    route = _route()
    settings = RestClientSettings(base_url=BASE_REST_URL)

    with EbarimtRestClient(settings, headers={"X-Api-Key": "client"}) as client:
        client.bank_accounts.read(tin=TIN, headers={"X-Api-Key": "override"})

    # httpx merges per-request headers over client defaults, request wins.
    assert route.calls.last.request.headers["x-api-key"] == "override"


@respx.mock
def test_injected_sync_client_receives_client_headers() -> None:
    route = _route()
    settings = RestClientSettings(base_url=BASE_REST_URL)
    injected = httpx.Client(base_url=BASE_REST_URL)

    client = EbarimtRestClient(settings, sync_client=injected, headers={"X-Api-Key": "k"})
    try:
        client.bank_accounts.read(tin=TIN)
    finally:
        injected.close()

    # Client-level headers are applied to the injected client's defaults too.
    assert injected.headers["x-api-key"] == "k"
    assert route.calls.last.request.headers["x-api-key"] == "k"


@pytest.mark.asyncio
@respx.mock
async def test_injected_async_client_receives_client_headers() -> None:
    route = _route()
    settings = RestClientSettings(base_url=BASE_REST_URL)
    injected = httpx.AsyncClient(base_url=BASE_REST_URL)

    client = EbarimtRestClient(settings, async_client=injected, headers={"X-Api-Key": "k"})
    try:
        await client.bank_accounts.aread(tin=TIN)
    finally:
        await injected.aclose()

    assert injected.headers["x-api-key"] == "k"
    assert route.calls.last.request.headers["x-api-key"] == "k"
