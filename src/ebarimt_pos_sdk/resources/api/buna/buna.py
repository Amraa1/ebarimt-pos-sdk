from ...base_resource import BaseResource, HeaderTypes
from .schema import GetBunaResponse


class BunaResource(BaseResource):
    """БҮНА (Бараа, Үйлчилгээний Нэгдсэн Ангилал) classification lookup.

    Wraps ``GET /api/info/check/barcode/v2[/{code}...]``. The endpoint is
    hierarchical: call ``read()`` (no segments) to get the top-level
    "Салбар" list, then drill down by passing the code at each level as
    the next segment. Codes nest as prefixes:

        read()                      -> Салбар
        read("0")                   -> Дэд салбар of "0"
        read("0", "01")             -> Бүлэг of "01"
        read("0", "01", "011")      -> Анги
        read("0", "01", "011",
             "0111")                -> Дэд анги
        read("0", "01", "011",
             "0111", "01111")       -> БҮНА код
        read("0", "01", "011",
             "0111", "01111",
             "0111100")             -> Баркод list

    Note on the OpenAPI spec: the path template is documented as
    ``{p4}/{p5}/{p1}/{p2}/{p3}/{p6}`` with all six segments — that is a
    Stoplight modeling artifact, not the real call shape. The live API
    is variable-depth (0..6 segments) and segments go in logical
    top-down order, as verified directly against the production server:

        GET https://api.ebarimt.mn/api/info/check/barcode/v2     -> Салбар
        GET https://api.ebarimt.mn/api/info/check/barcode/v2/9   -> drills "9"

    Each segment is just the code of the level you are expanding; the
    parameter names p1..p6 in the spec are labels for "depth N" in
    logical order (p1=Салбар, p2=Дэд салбар, …, p6=БҮНА код), regardless
    of how they appear in the URL template.
    """

    @property
    def _path(self) -> str:
        return "/api/info/check/barcode/v2"

    @staticmethod
    def _validate_segments(segments: tuple[str, ...]) -> None:
        for i, s in enumerate(segments):
            if not isinstance(s, str) or not s.strip():
                raise ValueError(
                    f"BunaResource: segment #{i} must be a non-empty string, got {s!r}"
                )

    def _build_path(self, segments: tuple[str, ...]) -> str:
        self._validate_segments(segments)
        if not segments:
            return self._path
        return self._path + "/" + "/".join(s.strip() for s in segments)

    def read(self, *segments: str, headers: HeaderTypes | None = None) -> GetBunaResponse:
        return self._send_sync_request(
            "GET",
            path=self._build_path(segments),
            headers=headers,
            response_model=GetBunaResponse,
        )

    async def aread(self, *segments: str, headers: HeaderTypes | None = None) -> GetBunaResponse:
        return await self._send_async_request(
            "GET",
            path=self._build_path(segments),
            headers=headers,
            response_model=GetBunaResponse,
        )
