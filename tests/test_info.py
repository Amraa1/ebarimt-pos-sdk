import httpx
import pytest
import respx

from ebarimt_pos_sdk import PosApiClient, PosApiSettings

SUCCESS_RESPONSE = httpx.Response(
    200,
    json={
        "operatorName": "TEST OPERATOR 1",
        "operatorTIN": "37900846788",
        "posId": 101321077,
        "posNo": "10012619",
        "version": "3.2.35",
        "lastSentDate": "2026-01-28 15:03:27",
        "leftLotteries": 19992,
        "appInfo": {
            "applicationDir": "C:\\Program Files (x86)\\PosAPI",
            "currentDir": "C:\\Program Files (x86)\\PosAPI",
            "database": "QSQLITE",
            "database-host": "127.0.0.1",
            "supported-databases": ["QSQLITE", "QMYSQL", "QSQLSERVER", "QPSQL"],
            "workDir": "C:\\Program Files (x86)\\PosAPI",
        },
        "paymentTypes": [
            {"code": "CASH", "name": "Бэлэнээр"},
            {"code": "PAYMENT_CARD", "name": "Төлбөрийн карт"},
            {"code": "BONUS_CARD_TEST", "name": "Бонус Карт тест"},
            {"code": "EMD", "name": "Эрүүл мэндийн даатгалаар"},
            {"code": "BANK_TRANSFER", "name": "Банкны шилжүүлэг"},
        ],
        "merchants": [
            {
                "tin": "37900846788",
                "name": "ТЕСТИЙН ХЭРЭГЛЭГЧ 1",
                "vatPayer": True,
                "customers": [
                    {"tin": "37900846788", "name": "ТЕСТИЙН ХЭРЭГЛЭГЧ 1", "vatPayer": True},
                    {"tin": "30000000000", "name": "ЭЦСИЙН ХЭРЭГЛЭГЧ", "vatPayer": False},
                    {"tin": "61101326127", "name": "ДАТАКЕЙР", "vatPayer": True},
                    {"tin": "61200064714", "name": "ТТҮГ-тест", "vatPayer": True},
                    {"tin": "630188132539", "name": "РЭГДЭНШАРАВ", "vatPayer": False},
                ],
            },
            {
                "tin": "61200064714",
                "name": "ТТҮГ-тест",
                "vatPayer": True,
                "customers": [
                    {"tin": "61200064714", "name": "ТТҮГ-тест", "vatPayer": True},
                    {"tin": "30000000000", "name": "ЭЦСИЙН ХЭРЭГЛЭГЧ", "vatPayer": False},
                ],
            },
        ],
        "condition": {"isMedicine": False},
    },
)


@pytest.mark.asyncio
@respx.mock
async def test_info_read_async_ok() -> None:
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(return_value=SUCCESS_RESPONSE)

    async with PosApiClient(settings) as client:
        resp = await client.info.aread()
        assert resp.operator_name == "TEST OPERATOR 1"
        assert route.called


@respx.mock
def test_info_read_sync_ok() -> None:
    base_url = "http://localhost:7080"
    settings = PosApiSettings(base_url=base_url)

    route = respx.get(f"{base_url}/rest/info").mock(return_value=SUCCESS_RESPONSE)

    client = PosApiClient(settings)

    resp = client.info.read()
    assert resp.operator_name == "TEST OPERATOR 1"
    assert route.called
