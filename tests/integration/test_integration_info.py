import pytest
from ..helpers import BASE_REST_URL
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings


@pytest.mark.integration
def test_integration_info_read_ok():
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url)

    client = EbarimtRestClient(settings)

    resp = client.info.read()
    assert resp.operator_name == "TEST OPERATOR 1"
