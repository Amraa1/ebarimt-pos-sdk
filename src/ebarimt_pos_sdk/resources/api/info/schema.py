from typing import Any

from pydantic import field_validator

from ...base_model import BaseEbarimtModel


class GetTinInfoResponse(BaseEbarimtModel):
    msg: str
    status: int
    data: str

    @field_validator("data", mode="before")
    @classmethod
    def ensure_string(cls, v: Any) -> str:
        return str(v)
