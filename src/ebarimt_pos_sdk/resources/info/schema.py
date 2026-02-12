from __future__ import annotations

from pydantic import Field

from ..resource import BaseEbarimtModel


class AppInfo(BaseEbarimtModel):
    """Runtime and environment information of the PosAPI application."""

    application_dir: str = Field(description="Installation directory of the PosAPI application.")
    current_dir: str = Field(description="Current working directory of the PosAPI process.")
    database: str = Field(description="Database driver currently in use.")
    database_host: str = Field(description="Database host or file path (for SQLite).")
    supported_databases: list[str] = Field(description="List of supported database types.")
    work_dir: str = Field(description="Working directory used by PosAPI.")


class RestInfoCustomer(BaseEbarimtModel):
    """Customer organization registered under the merchant."""

    name: str = Field(description="Customer organization name.")
    tin: str = Field(description="Customer Tax Identification Number (TIN).")
    vat_payer: bool = Field(
        description="Indicates whether the customer is registered as a VAT payer."
    )


class Merchant(BaseEbarimtModel):
    """Merchant organization registered in PosAPI."""

    name: str = Field(description="Merchant organization name.")
    tin: str = Field(description="Merchant Tax Identification Number (TIN).")
    customers: list[RestInfoCustomer] = Field(
        description="List of customer organizations associated with the merchant."
    )


class ReadInfoResponse(BaseEbarimtModel):
    """Response returned from GET /rest/info containing PosAPI system information."""

    operator_name: str = Field(description="Name of the PosAPI operator organization.")
    operator_tin: str = Field(description="Tax Identification Number (TIN) of the operator.")
    pos_id: float = Field(description="Unique identifier of the PosAPI instance.")
    pos_no: str = Field(description="POS number assigned to this PosAPI instance.")
    last_sent_date: str = Field(description="Timestamp of the last successfully submitted receipt.")
    left_lotteries: int = Field(description="Number of remaining lottery codes available.")
    app_info: AppInfo = Field(description="PosAPI application runtime information.")
    merchants: list[Merchant] = Field(
        description="List of merchant organizations registered in this PosAPI instance."
    )
