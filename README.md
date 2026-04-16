# ebarimt-pos-sdk

[![codecov](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk/graph/badge.svg?token=EZ18HFDG46)](https://codecov.io/gh/Amraa1/ebarimt-pos-sdk)

Modern async-first Python SDK for Ebarimt Pos API 3.0.

> [Project doc](https://ebarimt-pos-sdk.readthedocs.io/mn/latest/)  
> Ebarimt Pos API 3.0 [documentation](https://developer.itc.gov.mn/docs/ebarimt-api/inbishdm2zj3x-pos-api-3-0-sistemijn-api-holbolt-zaavruud)

## Quick Start

### REST client — create a receipt

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
                "name": "Product",
                "measure_unit": "ш",
                "qty": 1,
                "unit_price": 10000,
                "total_amount": 10000,
            }],
        }],
    })
    print(receipt.id, receipt.qr_data)
```

Async version — replace `with` → `async with` and `client.receipt.create` → `await client.receipt.acreate`.

### API client — fetch TIN info

```python
from ebarimt_pos_sdk import EbarimtApiClient, ApiClientSettings

settings = ApiClientSettings(
    base_url="https://api.ebarimt.mn",
    token_url="https://auth.ebarimt.mn/token",
    client_id="your_client_id",
    username="your_username",
    password="your_password",
)

with EbarimtApiClient(settings=settings) as client:
    info = client.tin_info.read("1234567890")
    print(info.data)
```

---

## Development setup

```bash
uv sync --dev
uv run pytest
```

## PosAPI тохируулах

PosAPI нь суусны дараа анхны байдлаар тохируулах шаардлагатай. “posapi.ini”
файлд тухайн PosAPI-н үндсэн тохиргоо байрлах ба “P101.poi, P102.poi” файлуудад
ажиллагааны тохиргоо байрлах ба нууцлагдсан байна.

### Үндсэн тохиргооны тайлбар /posapi.ini файл/

| Нэр              | Тайлбар                                                        |
| ---------------- | -------------------------------------------------------------- |
| authUrl          |                                                                |
| authRealm        | Тухайн PosAPI-н нэгдсэн нэвтрэлттэй холбогдох тохиргоо         |
| authClientId     | Өөрчлөх шаардлагагүй.                                          |
| authClientSecret |                                                                |
| ebarimtUrl       | Ebarimt системтэй холбогдох хаяг Өөрчлөх шаардлагагүй          |
| db               | Өгөгдлийн сангийн driver                                       |
| dbHost           | Өгөгдлийн сангийн хаяг Хэрэв QSQLITE бол файлын зам байна      |
| dbPort           | Өгөгдлийн сангийн port Хэрэв QSQLITE бол бөглөхгүй             |
| dbUser           | Өгөгдлийн сангийн хэрэглэгчийн нэр Хэрэв QSQLITE бол бөглөхгүй |
| dbPass           | Өгөгдлийн сангийн нууц үг хэрэв QSQLITE бол бөглөхгүй          |
| dbName           | Өгөгдлийн сангийн баазын нэр Хэрэв QSQLITE бол бөглөхгүй       |
| dbOptions        | Өгөгдлийн сангийн нэмэлт тохиргоо Хэрэв QSQLITE бол бөглөхгүй  |
| workDir          | PosAPI-н ажиллагааны хавтас                                    |
| webServiceHost   | PosAPI-н ажиллах сүлжээний IP address                          |
| webServicePort   | PosAPI-н ажиллах сүлжээний port                                |

**WorkDir** хавтсанд ажиллагааны тохиргоо байрлах ба уг тохиргооны файлуудын агуулга
нь тогтмол өөрчлөгдөж байх тул PosAPI ажиллуулж буй хэрэглэгч нь унших, бичих
эрхтэй байхыг анхаарана уу. Мөн уг хавтсыг ямар ч нөхцөлд **FREEZE хийх ёсгүй**
гэдгийг анхаарна уу.

### PosAPI-н дэмжиж ажиллах өгөгдлийн сангууд ба driver-ууд

| Нэр     | Тайлбар                       |
| ------- | ----------------------------- |
| QMYSQL  | MySQL эсвэл MariaDB           |
| QPSQL   | PostgreSQL                    |
| QODBC   | ODBC for Microsoft SQL Server |
| QSQLITE | SQLite version 3              |

PosAPI нь ачааллах үедээ өгөгдлийн сангийн table-г автоматаар өөрөө үүсгэдэг тул
тухайн хэрэглэгч нь table үүсгэх эрх бүхий хэрэглэгч байх шаардлагатайг анхаарна уу
