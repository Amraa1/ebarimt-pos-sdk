from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AppInfo(BaseModel):
    """
    PosAPI-н ерөнхий мэдээлэл.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    application_dir: str = Field(alias="applicationDir", description="Файл байршиж буй хавтас")
    current_dir: str = Field(alias="currentDir", description="Файл байршиж буй хавтас")
    database: str = Field(description="Баазын driver /Qt5 тохиргоогоор/")
    database_host: str = Field(
        alias="database-host", description="Баазын хаяг /sqlite бол файлын зам/"
    )
    work_dir: str = Field(alias="workDir", description="Ажиллаж буй хавтас")


class RestInfoCustomer(BaseModel):
    """
    Үйлчлүүлэгч ААН.
    """

    name: str = Field(description="ААН-нэр")
    tin: str = Field(description="ААН-н ТТД")
    vat_payer: bool = Field(
        alias="vatPayer",
        description="НӨАТ суутган төлөгч мөн эсэх\ntrue: НӨАТ суутган төлөгч мөн\nfalse: НӨАТ суутган төлөгч биш",
    )


class Merchant(BaseModel):
    """
    PosAPI-д бүртгэлтэй ААН.
    """

    name: str = Field(description="ААН-нэр")
    tin: str = Field(description="ААН-н ТТД")
    customers: list[RestInfoCustomer] = Field(description="Үйлчлүүлэгч ААН-н жагсаалт")


class ReadInfoResponse(BaseModel):
    """
    GET /rest/info (200 OK) response schema.
    """

    operator_name: str = Field(alias="operatorName", description="Оператор байгууллагын нэр")
    operator_tin: str = Field(alias="operatorTIN", description="Оператор байгууллагын ТТД")
    pos_id: float = Field(alias="posId", description="PosAPI-н систем дэх бүртгэлийн Id")
    pos_no: str = Field(alias="posNo", description="PosAPI-н систем дэх бүртгэлийн дугаар")
    last_sent_date: str = Field(
        alias="lastSentDate", description="Баримт илгээсэн огноо /Сүүлийн байдлаар/"
    )
    left_lotteries: int = Field(alias="leftLotteries", description="Нийт үлдсэн сугалаа")
    app_info: AppInfo = Field(alias="appInfo", description="PosAPI-н ерөнхий мэдээлэл")
    merchants: list[Merchant] = Field(description="PosAPI-д бүртгэлтэй ААН-н жагсаалт")

    model_config = ConfigDict(populate_by_name=True)
