import pytest

from ebarimt_pos_sdk import PosApiClient, PosApiSettings


@pytest.mark.integration
def test_integration_bank_accounts_read_sync_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url, default_headers=None)
    tin = "37900846788"

    with PosApiClient(settings) as client:
        resp = client.bank_accounts.read(tin=tin)
        assert resp[0].tin == tin
