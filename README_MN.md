# ebarimt-pos-sdk

[![codecov](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk/graph/badge.svg?token=EZ18HFDG46)](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Ebarimt POS API 3.0** -тай ажиллах зориулалттай, async эхлэлтэй орчин үеийн Python SDK. OAuth2-оор хамгаалагдсан олон
нийтийн API болон POS төхөөрөмж дээр ажилладаг дотоод REST API-г хоёуланг нь нэгдсэн, төрөлжсэн, эвтэйхэн интерфэйсээр
бүрхэж өгдөг.

> 📖 Баримт бичиг: [Монгол](https://ebarimt-pos-sdk.readthedocs.io/mn/latest/) ·
> [English](https://ebarimt-pos-sdk.readthedocs.io/en/latest/) 📘 Ebarimt POS API 3.0 заавар:
> <https://developer.itc.gov.mn/docs/ebarimt-api/inbishdm2zj3x-pos-api-3-0-sistemijn-api-holbolt-zaavruud> 🇬🇧 English
> version: [README.md](./README.md)

---

## Онцлог

- **Async-first** — үйлдэл бүр синхрон болон `async` хувилбартай (`method()` / `amethod()`). `httpx` дээр суурилсан.
- **Хатуу төрөлтэй** — Pydantic v2 загварууд, camelCase ↔ snake_case хөрвүүлэгчтэй. `ty`-ээр төрөл шалгасан.
- **Хоёр тусгайлсан клиент** — олон нийтийн eBarimt API-д `EbarimtApiClient` (нэвтрэх мэдээлэл шаардлагагүй),
  дотоод POS REST API-д `EbarimtRestClient`.
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
    receipt = client.receipt.create(
        {
            "branch_no": "001",
            "total_amount": 10000,
            "merchant_tin": "1234567890",
            "pos_no": "POS001",
            "type": "B2C_RECEIPT",
            "bill_id_suffix": "A",
            "receipts": [
                {
                    "total_amount": 10000,
                    "tax_type": "VAT_ABLE",
                    "merchant_tin": "1234567890",
                    "items": [
                        {
                            "name": "Бараа",
                            "measure_unit": "ш",
                            "qty": 1,
                            "unit_price": 10000,
                            "total_amount": 10000,
                        }
                    ],
                }
            ],
        }
    )
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
)

with EbarimtApiClient(settings=settings) as client:
    info = client.tin_info.read("1234567890")
    print(info.data)
```

#### POS-доо мерчант бүртгэх

Оператор өөрийн POS-д мерчантыг operator portal ашиглахгүйгээр бүртгүүлж болно. Нэвтрэх мэдээлэл шаарддаг цорын ганц
дуудлага нь энэ: OAuth2 password grant нэвтрэлт болон eBarimt-аас олгосон `X-API-KEY`.

```python
from ebarimt_pos_sdk import CreateMerchantRegistrationRequest

settings = create_api_settings(
    Environment.STAGING,
    client_id="your_client_id",
    username="your_username",
    password="your_password",
    api_key="your_api_key",
)

with EbarimtApiClient(settings) as client:
    ack = client.merchant_registration.create(
        CreateMerchantRegistrationRequest(pos_no="10005299", merchant_tins=["77001059076"])
    )
```

Энэ дуудлага зөвхөн хүсэлт *илгээнэ*; eBarimt дараа нь баталгаажуулна. TIN нь POS-ийн мерчантуудын жагсаалтад гарч
ирэх хүртэл `EbarimtRestClient.info.read()`-ийг давтан шалгана. Нэвтрэх мэдээлэл дутуу бол юу ч илгээхээс өмнө
`PosApiConfigurationError` гарна; татгалзвал eBarimt-ийн мессежтэй `PosApiBusinessError` гарна.

---

## Клиентүүдийн тойм

| Клиент              | Нэвтрэлт               | Боломжит resource-ууд                                            |
| ------------------- | ---------------------- | ---------------------------------------------------------------- |
| `EbarimtRestClient` | Байхгүй (дотоод сүлж.) | `receipt`, `info`, `send_data`, `bank_accounts`                  |
| `EbarimtApiClient`  | Байхгүй (нийтийн API)¹ | `district_code`, `tin_info`, `merchant_info`, `product_tax_code`, `buna`, `merchant_registration` |

¹ `merchant_registration`-аас бусад нь. Тэр нь OAuth2 password grant нэвтрэлт болон API key шаарддаг.

Хоёр клиент хоёулаа синхрон болон асинхрон context manager-ийг дэмжих ба settings (timeout, TLS, header, retry policy)
болон алдааны иерархийг хуваалцана.

---

## Алдаа шийдвэрлэх

SDK нь алдааг тодорхой иерархиар илэрхийлдэг тул та өөрийн кодын түвшинд тохируулан хариу үйлдэл хийх боломжтой:

```text
PosApiError
├── PosApiTransportError      # сүлжээ / timeout / DNS / TLS
├── PosApiDecodeError         # JSON хариу буруу байна
├── PosApiHttpError           # сервер 2xx бус хариу буцаав
├── PosApiBusinessError       # 2xx гэвч бизнес логикийн алдаа
├── PosApiValidationError     # Pydantic validation алдаа
└── PosApiConfigurationError  # шаардлагатай тохиргоо дутуу; хүсэлт илгээгдээгүй
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
except PosApiTransportError as e:
    # Сүлжээний түвшин. e.cause нь httpx-ийн анхдагч алдаа.
    if not e.request_sent:
        # Хүсэлт клиентээс гараагүй (холболт татгалзсан, DNS, холболтын timeout,
        # proxy татгалзсан, OAuth токен авч чадаагүй): PosAPI энэ баримтыг
        # хадгалсан байх боломжгүй тул дахин илгээхэд аюулгүй.
        ...
    else:
        # Хүсэлт PosAPI-д хүрсэн байж магадгүй, хариу нь алга болсон (read
        # timeout, холболт тасарсан, ...). receipt.create зэрэг POST-ийн хувьд
        # баримт аль хэдийн үүссэн байж болзошгүй: дахин илгээхээс өмнө нягтал,
        # эс бөгөөс давхар е-баримт гарах эрсдэлтэй.
        raise
```

`request_sent` нь зөвхөн хүсэлт огт илгээгдээгүйг баталсан алдаанд `False` байна
(`httpx.ConnectError`, `httpx.ConnectTimeout`, `httpx.ProxyError`, эсвэл хүсэлтээс өмнөх токен
авалт амжилтгүй болсон). Бусад бүх тохиолдолд, үүнд SDK-д танигдаагүй алдаа ч орно, `True` байна.
Idempotent хүсэлтийг дахин оролдох үед алдаа нь сүүлийн оролдлогыг илэрхийлнэ.

Алдаа print хийхэд `Authorization` header болон токен агуулсан query параметрүүд автоматаар нуугдсан байна.

---

## Тохиргоо

Бүх settings нь өөрчлөгдөшгүй (immutable) dataclass-ууд — нэг удаа үүсгээд клиентэд дамжуулна. Timeout, TLS
баталгаажуулалт, retry-ийн зан төлөв нь хоёр клиентэд `BaseSettings`-ээр дамжуулан нийтлэг. Нэмэлт header-ийг клиентийн
байгуулагчид дамжуулна: `EbarimtRestClient(settings, headers={"X-Request-Source": "pos-42"})`.

```python
from ebarimt_pos_sdk import RestClientSettings
from ebarimt_pos_sdk.settings import RetrySettings

settings = RestClientSettings(
    base_url="http://localhost:1234",
    timeout_s=5.0,
    verify_tls=True,
    retry=RetrySettings(
        max_retries=3,
        backoff_base_seconds=1.0,
        max_backoff_seconds=30.0,
        jitter=True,  # full jitter: sleep ~ U(0, backoff)
        respect_retry_after=True,  # серверийн Retry-After давуу (дээд хязгаартай)
        retryable_statuses=frozenset({429, 500, 502, 503, 504}),
        retry_methods=RetrySettings.DEFAULT_RETRY_METHODS,  # GET/HEAD/OPTIONS/PUT/DELETE
        retry_unsent=False,  # True: POST/PATCH-ийг зөвхөн клиентээс гараагүй үед дахин илгээнэ
    ),
)
```

Үндсэн retry policy — 429/5xx болон сүлжээний алдаанд jitter-тэй экспоненциал backoff бүхий 3 оролдлого — ихэнх
тохиолдолд тохиромжтой. *Full jitter* (`[0, backoff]` завсраас санамсаргүй утга) олон POS төхөөрөмж нэгэн зэрэг
алдаа гарахад бүгд зэрэг дахин оролдохоос сэргийлнэ; серверийн `Retry-After` header (секунд эсвэл HTTP-date) тооцсон
backoff-ыг орлох ба `max_backoff_seconds`-оор хязгаарлагдана. Тестэд тогтмол хугацаа хэрэгтэй бол `jitter=False`.

**Retry зөвхөн idempotent method-уудад үйлчилнэ.** `receipt.create` нь `POST` хүсэлт: PosAPI баримтыг хадгалсан ч
хариу timeout-оор алдагдвал дахин илгээснээр *давхар* е-баримт үүснэ. Тиймээс SDK `POST` (болон `PATCH`) хүсэлтийг
`max_retries`-ээс үл хамааран яг нэг удаа илгээнэ. Давхардлыг илрүүлж чаддаг бол дараах байдлаар идэвхжүүлнэ:

```python
RetrySettings(retry_methods=RetrySettings.DEFAULT_RETRY_METHODS | {"POST"})
```

Илүү аюулгүй дунд хувилбар нь `retry_unsent=True`. Энэ нь `POST`/`PATCH`-ийг зөвхөн хүсэлт клиентээс огт
гараагүйг баталсан алдааны дараа дахин илгээнэ: холболт татгалзсан, DNS алдаа, холболтын timeout, эсвэл proxy
tunnel-ийг татгалзсан (`PosApiTransportError.request_sent` нь `False` байх тохиолдлууд). PosAPI хүлээж аваагүй
баримтыг хадгалах боломжгүй тул давхардал үүсэхгүй. Бусад бүх тохиолдол эхний оролдлогоор дуусна, үүнд ямар ч
хариу (`503` ч гэсэн) болон хүсэлт илгээгдсэн байж болзошгүй алдаа (read timeout, холболт тасарсан) орно:

```python
RetrySettings(retry_unsent=True)  # жишээ нь POS түр холбогдохгүй байхад тэсвэрлэх
```

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

# Төрөл шалгах
uv run ty check
```

Integration тестүүд (`@pytest.mark.integration` тэмдэгтэй) нь амьд PosAPI сервер болон нэвтрэх мэдээллийг шаардах тул
CI-д ажиллахгүй.

Гишүүнчлэлийн заавар [CONTRIBUTING.md](./CONTRIBUTING.md)-ээс, хувилбарын түүх [CHANGELOG.md](./CHANGELOG.md)-ээс.

---

## Лиценз

[MIT License](./LICENSE)-ээр нийтлэгдсэн.
