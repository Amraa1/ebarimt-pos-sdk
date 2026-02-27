from pydantic import BaseModel, ConfigDict

WHITE_LIST = {
    "terminal_id": "terminalID",
    "iban": "iBan",
    "total_vat": "totalVAT",
    "operator_tin": "operatorTIN",
    "database_host": "database-host",
    "supported_databases": "supported-databases",
}


def alias_generator(s: str) -> str:
    if s in WHITE_LIST:
        return WHITE_LIST[s]

    parts = s.split("_")
    first = parts[0]
    rest: list[str] = []

    for word in parts[1:]:
        rest.append(word.title())

    return first + "".join(rest)


class BaseEbarimtModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        alias_generator=alias_generator,
        validate_by_name=True,  # allow snake_case input
        validate_by_alias=True,  # also allow camelCase input
    )
