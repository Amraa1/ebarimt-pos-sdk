import httpx
import pytest
import respx

from ebarimt_pos_sdk import ApiClientSettings, EbarimtApiClient

from ..data.buna import BARCODE_RESPONSE, SUB_BRANCH_RESPONSE, TOP_LEVEL_RESPONSE
from ..helpers import BASE_API_URL

BUNA_PATH = "/api/info/check/barcode/v2"


def _settings() -> ApiClientSettings:
    return ApiClientSettings(base_url=BASE_API_URL)


@respx.mock
def test_buna_top_level_sync_ok() -> None:
    route = respx.get(f"{BASE_API_URL}{BUNA_PATH}").mock(
        return_value=httpx.Response(status_code=200, json=TOP_LEVEL_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.buna.read()
        assert route.called
        assert resp.root[0] == [
            "0",
            "Хөдөө аж ахуй, ойн аж ахуй, загас агнуурын бүтээгдэхүүн ",
        ]


@respx.mock
def test_buna_drill_down_sync_ok() -> None:
    route = respx.get(f"{BASE_API_URL}{BUNA_PATH}/0").mock(
        return_value=httpx.Response(status_code=200, json=SUB_BRANCH_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.buna.read("0")
        assert route.called
        assert [row[0] for row in resp.root] == ["01", "02", "03", "04"]


@respx.mock
def test_buna_barcode_level_sync_ok() -> None:
    full = f"{BASE_API_URL}{BUNA_PATH}/0/01/011/0111/01111/0111100"
    route = respx.get(full).mock(
        return_value=httpx.Response(status_code=200, json=BARCODE_RESPONSE)
    )
    with EbarimtApiClient(settings=_settings()) as client:
        resp = client.buna.read("0", "01", "011", "0111", "01111", "0111100")
        assert route.called
        # Leaf rows include barcode, name, registered date.
        assert resp.root[0][0] == "800888883000"
        assert len(resp.root[0]) == 3


@pytest.mark.asyncio
@respx.mock
async def test_buna_top_level_async_ok() -> None:
    route = respx.get(f"{BASE_API_URL}{BUNA_PATH}").mock(
        return_value=httpx.Response(status_code=200, json=TOP_LEVEL_RESPONSE)
    )
    async with EbarimtApiClient(settings=_settings()) as client:
        resp = await client.buna.aread()
        assert route.called
        assert len(resp.root) == 3


@pytest.mark.asyncio
@respx.mock
async def test_buna_drill_down_async_ok() -> None:
    route = respx.get(f"{BASE_API_URL}{BUNA_PATH}/0/01").mock(
        return_value=httpx.Response(status_code=200, json=SUB_BRANCH_RESPONSE)
    )
    async with EbarimtApiClient(settings=_settings()) as client:
        resp = await client.buna.aread("0", "01")
        assert route.called
        assert resp.root[0][0] == "01"


def test_buna_rejects_blank_segment() -> None:
    with EbarimtApiClient(settings=_settings()) as client:
        with pytest.raises(ValueError, match="segment #1"):
            client.buna.read("0", "  ")
