import httpx
import pytest
import respx

from ebarimt_pos_sdk import PosApiClient, PosApiSettings

SUCCESS_RESPONSE = httpx.Response(
    200,
    json=[
        {
            "id": 302193,
            "tin": "37900846788",
            "bankAccountNo": "499037985",
            "bankAccountName": "Тестийн хэрэглэгч 1",
            "bankId": 0,
            "bankName": "",
            "iBan": "",
        },
        {
            "id": 302194,
            "tin": "37900846788",
            "bankAccountNo": "1102046833",
            "bankAccountName": "Тестийн хэрэглэгч 1",
            "bankId": 0,
            "bankName": "",
            "iBan": "",
        },
        {
            "id": 302195,
            "tin": "37900846788",
            "bankAccountNo": "4990037827",
            "bankAccountName": "Тестийн хэрэглэгч 1",
            "bankId": 0,
            "bankName": "",
            "iBan": "10001004990037827",
        },
        {
            "id": 302196,
            "tin": "37900846788",
            "bankAccountNo": "1102113722",
            "bankAccountName": "Тестийн хэрэглэгч 1",
            "bankId": 0,
            "bankName": "",
            "iBan": "",
        },
        {
            "id": 302197,
            "tin": "37900846788",
            "bankAccountNo": "5270461217",
            "bankAccountName": "харилцах",
            "bankId": 0,
            "bankName": "",
            "iBan": "",
        },
        {
            "id": 302198,
            "tin": "37900846788",
            "bankAccountNo": "777",
            "bankAccountName": "777 test bank",
            "bankId": 0,
            "bankName": "",
            "iBan": "",
        },
    ],
)


@respx.mock
def test_bank_accounts_read_sync_ok() -> None:
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url, default_headers=None)
    tin = "37900846788"

    route = respx.get(f"{base_url}/rest/bankAccounts").mock(return_value=SUCCESS_RESPONSE)

    with PosApiClient(settings) as client:
        resp = client.bank_accounts.read(tin=tin)
        assert resp[0].tin == tin
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_bank_accounts_read_async_ok()-> None:
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)
    tin = "37900846788"

    route = respx.get(f"{base_url}/rest/bankAccounts").mock(return_value=SUCCESS_RESPONSE)

    with PosApiClient(settings) as client:
        resp = await client.bank_accounts.aread(tin=tin)
        assert resp[0].tin == tin
        assert route.called
