from ...resource import BaseEbarimtModel


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
    data: int
