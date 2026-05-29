from datetime import date

import httpx
import pytest
import respx

from ebarimt_pos_sdk import ApiClientSettings, EbarimtApiClient

from ..data.merchant_info import (
    NON_VATPAYER_RESPONSE,
    NOT_FOUND_RESPONSE,
    NULL_GOVERNMENT_RESPONSE,
    SUCCESS_RESPONSE,
)
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


@respx.mock
def test_merchant_info_null_registered_date() -> None:
    # Non-VAT-payers come back with a null vatpayerRegisteredDate; the SDK must
    # accept the response rather than raising a validation error.
    route = respx.get(f"{BASE_API_URL}/api/info/check/getInfo").mock(
        return_value=httpx.Response(status_code=200, json=NON_VATPAYER_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.merchant_info.read("01234567891")
        assert resp.data is not None
        assert resp.data.vatpayer_registered_date is None
        assert resp.data.vat_payer is False
        assert route.called


@respx.mock
def test_merchant_info_null_is_government() -> None:
    # The server may return a null isGovernment flag; the SDK must accept it
    # rather than raising a validation error (issue #74).
    route = respx.get(f"{BASE_API_URL}/api/info/check/getInfo").mock(
        return_value=httpx.Response(status_code=200, json=NULL_GOVERNMENT_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.merchant_info.read("01234567891")
        assert resp.data is not None
        assert resp.data.is_government is None
        assert route.called


@respx.mock
def test_merchant_info_null_data() -> None:
    # An unknown TIN yields a 200 with a null data object.
    route = respx.get(f"{BASE_API_URL}/api/info/check/getInfo").mock(
        return_value=httpx.Response(status_code=200, json=NOT_FOUND_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.merchant_info.read("00000000000")
        assert resp.data is None
        assert resp.status == 200
        assert route.called
