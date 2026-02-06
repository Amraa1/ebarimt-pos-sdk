import pytest

from ebarimt_pos_sdk import PosApiClient, PosApiSettings


@pytest.mark.integration
def test_integration_info_read_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    client = PosApiClient(settings)

    resp = client.info.read()
    assert resp.operator_name == "TEST OPERATOR 1"
