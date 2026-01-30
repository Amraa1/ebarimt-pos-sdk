import httpx
import respx

from ebarimt_pos_sdk import PosApiClient, PosApiSettings


@respx.mock
def test_bank_accounts_read_ok():
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)
    tin = "77001059076"

    route = respx.get(f"{base_url}/rest/bankAccounts").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 2,
                    "tin": tin,
                    "iBan": "12123129831982319283",
                    "bankAccountNo": "129831982319283",
                    "bankAccountName": "Ebarimt Pos SDK Test",
                    "bankId": 1,
                    "bankName": "SDK Bank",
                    "data": {},
                },
            ],
        )
    )

    with PosApiClient(settings) as client:
        resp = client.bank_accounts.read(tin=tin)
        assert resp[0].tin == tin
        assert route.called
