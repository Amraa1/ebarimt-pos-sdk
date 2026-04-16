import httpx
import pytest
import respx

from ebarimt_pos_sdk import EbarimtRestClient, PosApiHttpError, RestClientSettings

from ..data.info import SUCCESS_RESPONSE
from ..helpers import BASE_REST_URL


@pytest.mark.asyncio
@respx.mock
async def test_info_read_async_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(
        return_value=httpx.Response(
            200,
            json=SUCCESS_RESPONSE,
        )
    )

    async with EbarimtRestClient(settings) as client:
        resp = await client.info.aread()
        assert resp.operator_name == "TEST OPERATOR 1"
        assert route.called


@respx.mock
def test_info_read_sync_ok() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(
        return_value=httpx.Response(
            200,
            json=SUCCESS_RESPONSE,
        )
    )

    with EbarimtRestClient(settings) as client:
        resp = client.info.read()
        assert resp.operator_name == "TEST OPERATOR 1"
        assert route.called


@respx.mock
def test_info_read_sync_http_error_when_error_body_is_not_json() -> None:
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(
        return_value=httpx.Response(
            404,
            text="<html><body>Not Found</body></html>",
            headers={"content-type": "text/html"},
        )
    )

    with EbarimtRestClient(settings) as client:
        with pytest.raises(PosApiHttpError) as exc_info:
            client.info.read()

    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 404
    assert route.called
