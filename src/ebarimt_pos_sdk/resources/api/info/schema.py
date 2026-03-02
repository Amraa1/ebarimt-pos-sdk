from typing import Any

from pydantic import field_validator

from ...base_model import BaseEbarimtModel


class BranchInfo(BaseEbarimtModel):
    branch_code: str
    branch_name: str
    sub_branch_code: str
    sub_branch_name: str


class GetDistrictCodeResponse(BaseEbarimtModel):
    msg: str
    status: int
    data: list[BranchInfo]


class GetTinInfoResponse(BaseEbarimtModel):
    msg: str
    status: int
    data: str

    @field_validator("data", mode="before")
    @classmethod
    def ensure_string(cls, v: Any) -> str:
        return str(v)
