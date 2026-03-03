import pytest
from ..helpers import BASE_REST_URL, TIN
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings


@pytest.mark.integration
def test_integration_bank_accounts_read_sync_ok():
    base_url = BASE_REST_URL
    settings = RestClientSettings(base_url=base_url, headers=None)
    tin = TIN

    with EbarimtRestClient(settings) as client:
        resp = client.bank_accounts.read(tin=tin)
        assert resp[0].tin == tin
