# ebarimt-pos-sdk

[![codecov](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk/graph/badge.svg?token=EZ18HFDG46)](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Ebarimt POS API 3.0** -тай ажиллах зориулалттай, async эхлэлтэй орчин үеийн Python SDK. OAuth2-оор хамгаалагдсан олон
нийтийн API болон POS төхөөрөмж дээр ажилладаг дотоод REST API-г хоёуланг нь нэгдсэн, төрөлжсэн, эвтэйхэн интерфэйсээр
бүрхэж өгдөг.

> 📖 Албан ёсны баримт бичиг: <https://ebarimt-pos-sdk.readthedocs.io/mn/latest/> 📘 Ebarimt POS API 3.0 заавар:
> <https://developer.itc.gov.mn/docs/ebarimt-api/inbishdm2zj3x-pos-api-3-0-sistemijn-api-holbolt-zaavruud> 🇬🇧 English
> version: [README.md](./README.md)

---

## Онцлог

- **Async-first** — үйлдэл бүр синхрон болон `async` хувилбартай (`method()` / `amethod()`). `httpx` дээр суурилсан.
- **Хатуу төрөлтэй** — Pydantic v2 загварууд, camelCase ↔ snake_case хөрвүүлэгчтэй. `mypy --strict` горимд бүрэн
  нийцсэн.
- **Хоёр тусгайлсан клиент** — олон нийтийн OAuth2 API-д `EbarimtApiClient`, дотоод POS REST API-д `EbarimtRestClient`.
- **OAuth2 токен удирдлага** — password grant урсгал болон токен шинэчлэх (refresh) логик, хугацаа дуусахаас өмнө
  автоматаар шинэчилдэг.
- **Найдвартай тээвэрлэлт** — 5xx болон сүлжээний алдаанд экспоненциал backoff-той давтан оролдлого, хүсэлт бүрийн
  timeout, TLS баталгаажуулалт.
- **Зохион байгуулалттай алдаа** — тээвэр, HTTP, decode, validation, бизнес логикийн алдаануудыг тус тусад нь ялгасан
  иерархи. Authorization header болон токенууд алдааны мессеж дотор автоматаар нуугдана.
- **Орчны тохиргоо** — `create_api_settings`-р `STAGING` болон `PRODUCTION`-ийн хооронд нэг мөрөөр солих боломжтой.

---

## Суулгах

```bash
pip install ebarimt-pos-sdk
```

Эсвэл `uv`-ээр:

```bash
uv add ebarimt-pos-sdk
```

Python 3.10 ба түүнээс дээш хувилбар шаардана.

---

## Түргэн эхлэх

### Дотоод REST клиент — баримт үүсгэх

```python
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

settings = RestClientSettings(base_url="http://localhost:1234")

with EbarimtRestClient(settings) as client:
    receipt = client.receipt.create({
        "branch_no": "001",
        "total_amount": 10000,
        "merchant_tin": "1234567890",
        "pos_no": "POS001",
        "type": "B2C_RECEIPT",
        "bill_id_suffix": "A",
        "receipts": [{
            "total_amount": 10000,
            "tax_type": "VAT_ABLE",
            "merchant_tin": "1234567890",
            "items": [{
                "name": "Бараа",
                "measure_unit": "ш",
                "qty": 1,
                "unit_price": 10000,
                "total_amount": 10000,
            }],
        }],
    })
    print(receipt.id, receipt.qr_data)
```

Async хувилбар: `with`-ийг `async with` болгож, `await client.receipt.acreate(...)` гэж дуудна.

```python
import asyncio
from ebarimt_pos_sdk import EbarimtRestClient, RestClientSettings

async def main() -> None:
    async with EbarimtRestClient(RestClientSettings(base_url="http://localhost:1234")) as client:
        receipt = await client.receipt.acreate(payload)
        print(receipt.id)

asyncio.run(main())
```

### Олон нийтийн API клиент — ТТД хайх

URL-уудыг кодод шууд бичихгүйн тулд factory-г ашиглана:

```python
from ebarimt_pos_sdk import (
    EbarimtApiClient,
    Environment,
    create_api_settings,
)

settings = create_api_settings(
    Environment.PRODUCTION,  # эсвэл Environment.STAGING
    client_id="your_client_id",
    username="your_username",
    password="your_password",
)

with EbarimtApiClient(settings=settings) as client:
    info = client.tin_info.read("1234567890")
    print(info.data)
```

---

## Клиентүүдийн тойм

| Клиент              | Нэвтрэлт               | Боломжит resource-ууд                                            |
| ------------------- | ---------------------- | ---------------------------------------------------------------- |
| `EbarimtRestClient` | Байхгүй (дотоод сүлж.) | `receipt`, `info`, `send_data`, `bank_accounts`                  |
| `EbarimtApiClient`  | OAuth2 password grant  | `district_code`, `tin_info`, `merchant_info`, `product_tax_code` |

Хоёр клиент хоёулаа синхрон болон асинхрон context manager-ийг дэмжих ба settings (timeout, TLS, header, retry policy)
болон алдааны иерархийг хуваалцана.

---

## Алдаа шийдвэрлэх

SDK нь алдааг тодорхой иерархиар илэрхийлдэг тул та өөрийн кодын түвшинд тохируулан хариу үйлдэл хийх боломжтой:

```text
PosApiError
├── PosApiTransportError    # сүлжээ / timeout / DNS / TLS
├── PosApiDecodeError       # JSON хариу буруу байна
├── PosApiHttpError         # сервер 2xx бус хариу буцаав
├── PosApiBusinessError     # 2xx гэвч бизнес логикийн алдаа
└── PosApiValidationError   # Pydantic validation алдаа
```

```python
from ebarimt_pos_sdk import (
    PosApiBusinessError,
    PosApiHttpError,
    PosApiTransportError,
    PosApiValidationError,
)

try:
    receipt = client.receipt.create(payload)
except PosApiValidationError as e:
    # Бүтэц буруу — хүсэлтийг засаад дахин илгээнэ
    for err in e.errors:
        print(err["loc"], err["msg"])
except PosApiBusinessError as e:
    # Сервер хүлээн авсан ч бизнес дүрмээр татгалзав
    print(e.status, e.code, e.message)
except PosApiHttpError as e:
    # 4xx / 5xx — нууц мэдээлэл нуугдсан хүсэлт/хариу агуулсан
    print(e)
except PosApiTransportError:
    # Сүлжээний түвшин — дараа нь дахин оролдох боломжтой
    raise
```

Алдаа print хийхэд `Authorization` header болон токен агуулсан query параметрүүд автоматаар нуугдсан байна.

---

## Тохиргоо

Бүх settings нь өөрчлөгдөшгүй (immutable) dataclass-ууд — нэг удаа үүсгээд клиентэд дамжуулна. Timeout, TLS
баталгаажуулалт, нэмэлт header, retry-ийн зан төлөв нь хоёр клиентэд `BaseSettings`-ээр дамжуулан нийтлэг.

```python
from ebarimt_pos_sdk import RestClientSettings
from ebarimt_pos_sdk.settings import RetrySettings

settings = RestClientSettings(
    base_url="http://localhost:1234",
    timeout_s=5.0,
    verify_tls=True,
    headers={"X-Request-Source": "pos-42"},
    retry=RetrySettings(
        max_retries=3,
        backoff_base_seconds=1.0,
        retryable_statuses=frozenset({500, 502, 503, 504}),
    ),
)
```

Үндсэн retry policy — 5xx болон сүлжээний алдаанд экспоненциал backoff-той 3 оролдлого — ихэнх тохиолдолд тохиромжтой.

---

## Validation философи

SDK нь **бүтцийг шалгадаг, бодлогыг биш**:

- ✅ Талбайн хэлбэр, тогтвортой ID-ууд (ТТД, салбарын код)-ын regex, enum, энгийн тооны хязгаар (`>= 0`).
- ❌ Бизнес дүрэм, талбайн хоорондын хамаарал, лавлагаа хүснэгтийн шалгалт, байнга өөрчлөгддөг төрийн бодлого.

Энэ хил хязгаар нь санаатай. Бизнес дүрмийг сервер эзэмшиж, SDK нь бүтцийн зөв байдлыг эзэмшинэ. Энэ нь дүрэм
өөрчлөгдсөн үед SDK-г тогтвортой байлгана.

---

## Хөгжүүлэлтийн орчин

```bash
# Бүх хараат сан, dev extras-уудыг суулгах
uv sync --dev

# Unit тестүүдийг ажиллуулах
uv run pytest -m "not integration"

# Coverage-тай ажиллуулах
uv run pytest -m "not integration" --cov

# Lint, format
uv run ruff check
uv run ruff format

# Төрөл шалгах (strict)
uv run mypy src
```

Integration тестүүд (`@pytest.mark.integration` тэмдэгтэй) нь амьд PosAPI сервер болон нэвтрэх мэдээллийг шаардах тул
CI-д ажиллахгүй.

Гишүүнчлэлийн заавар [CONTRIBUTING.md](./CONTRIBUTING.md)-ээс, хувилбарын түүх [CHANGELOG.md](./CHANGELOG.md)-ээс.

---

## Лиценз

[MIT License](./LICENSE)-ээр нийтлэгдсэн.
