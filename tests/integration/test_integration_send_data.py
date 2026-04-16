import pytest

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

from ..helpers import BASE_REST_URL


@pytest.mark.integration
def test_integration_send_data_ok_sync():
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    with EbarimtRestClient(settings) as client:
        client.send_data.send()
