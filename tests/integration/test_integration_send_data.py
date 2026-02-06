import pytest

from ebarimt_pos_sdk import PosApiClient, PosApiSettings


@pytest.mark.integration
def test_integration_send_data_ok_sync():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    with PosApiClient(settings) as client:
        client.send_data.send()
