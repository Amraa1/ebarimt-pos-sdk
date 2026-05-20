import httpx
import pytest
import respx

from ebarimt_pos_sdk import ApiClientSettings, EbarimtApiClient

from ..data.product_tax_code import SUCCESS_RESPONSE
from ..helpers import BASE_API_URL


def _settings() -> ApiClientSettings:
    # Public ebarimt info endpoints don't require OAuth2; credentials omitted.
    return ApiClientSettings(base_url=BASE_API_URL)


@respx.mock
def test_product_tax_code_sync_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/receipt/receipt/getProductTaxCode").mock(
        return_value=httpx.Response(status_code=200, json=SUCCESS_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.product_tax_code.read()
        assert len(resp.data) > 0
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_product_tax_code_async_ok() -> None:
    route = respx.get(f"{BASE_API_URL}/api/receipt/receipt/getProductTaxCode").mock(
        return_value=httpx.Response(status_code=200, json=SUCCESS_RESPONSE)
    )
    async with EbarimtApiClient(settings=_settings()) as client:
        resp = await client.product_tax_code.aread()
        assert len(resp.data) > 0
        assert route.called
