from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SDKModel(BaseModel):
    """
    Base model for the SDK:
    - Allows forward/backward-compatible payload changes (extra keys allowed)
    - Clean developer ergonomics (aliases supported)
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        validate_assignment=False,
        str_strip_whitespace=True,
    )


class BankAccount(SDKModel):
    """
    Bank account record returned by GET /rest/bankAccounts.

    Note:
    - OpenAPI lists `iBan` as required, but some examples omit it.
      We keep it optional to avoid brittle SDK behavior.
    """

    id: int = Field(..., description="System-registered bank account ID.")
    tin: str = Field(..., description="Taxpayer identification number (TIN) of the account owner.")

    bank_account_no: str = Field(..., alias="bankAccountNo", description="Bank account number.")
    bank_account_name: str = Field(..., alias="bankAccountName", description="Bank account name.")

    bank_id: int = Field(..., alias="bankId", description="Bank ID.")
    bank_name: str = Field(..., alias="bankName", description="Bank name.")

    iban: str = Field(
        alias="iBan",
        description="International Bank Account Number (IBAN) / international account numbering.",
        examples=["100100015121212121111"],
    )

    # If the API sometimes returns a nested blob like `data: {}`, we keep it explicitly.
    data: dict[str, Any] | None = Field(default=None, description="Optional extra data payload.")
