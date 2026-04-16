"""
Tests that whitelisted alias fields round-trip correctly through serialization.

The WHITE_LIST in base_model.py maps snake_case Python names to hand-crafted
camelCase/acronym aliases. If any entry drifts from the actual API field name,
JSON output breaks silently. This file pins the contract.
"""

from ebarimt_pos_sdk.resources.base_model import WHITE_LIST, BaseEbarimtModel


class _AllAliasModel(BaseEbarimtModel):
    """Model that exercises every whitelisted alias field."""

    terminal_id: str = "T1"
    iban: str = "MN01"
    total_vat: float = 0.0
    operator_tin: str = "123"
    database_host: str = "localhost"
    supported_databases: str = "QSQLITE"


def test_whitelist_aliases_serialize_to_correct_json_keys() -> None:
    """Every whitelisted field must appear under its alias key in JSON output."""
    model = _AllAliasModel()
    data = model.model_dump(by_alias=True)

    for snake_name, alias in WHITE_LIST.items():
        assert alias in data, (
            f"Field '{snake_name}' should serialize as '{alias}' but key not found in output. "
            f"Output keys: {list(data.keys())}"
        )


def test_whitelist_aliases_deserialize_from_alias_keys() -> None:
    """Every whitelisted alias key must be accepted as input (uses string fields only)."""

    class _StringAliasModel(BaseEbarimtModel):
        terminal_id: str = ""
        iban: str = ""
        total_vat: str = ""
        operator_tin: str = ""
        database_host: str = ""
        supported_databases: str = ""

    payload = {alias: "value" for alias in WHITE_LIST.values()}
    model = _StringAliasModel.model_validate(payload)

    for snake_name in WHITE_LIST:
        assert getattr(model, snake_name) == "value", (
            f"Field '{snake_name}' was not populated from alias key '{WHITE_LIST[snake_name]}'"
        )


def test_standard_camelcase_alias_generator() -> None:
    """Non-whitelisted snake_case fields should convert to camelCase."""

    class _Model(BaseEbarimtModel):
        branch_no: str = "A1"
        total_amount: float = 100.0
        merchant_tin: str = "TIN"

    data = _Model().model_dump(by_alias=True)
    assert "branchNo" in data
    assert "totalAmount" in data
    assert "merchantTin" in data
