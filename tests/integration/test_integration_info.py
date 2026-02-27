import pytest

from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings


@pytest.mark.integration
def test_integration_info_read_ok():
    base_url = "http://localhost:7080"
    settings = RestClientSettings(base_url=base_url)

    client = EbarimtRestClient(settings)

    resp = client.info.read()
    assert resp.operator_name == "TEST OPERATOR 1"
