from pydantic import RootModel


class GetBunaResponse(RootModel[list[list[str]]]):
    """Hierarchical БҮНА (Бараа, Үйлчилгээний Нэгдсэн Ангилал) lookup.

    The response is a JSON array of rows. Each row is itself an array of
    strings whose shape depends on the level returned:

    - Classification rows (Салбар / Дэд салбар / Бүлэг / Анги / Дэд анги /
      БҮНА код): ``[code, name]``
    - Barcode rows (leaf level): ``[barcode, name, registered_date]``

    Per the SDK's "validate structure, not policy" rule we only assert that
    each row is a list of strings — interpretation is left to the caller.
    """
