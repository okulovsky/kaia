from pathlib import Path

from .result_type import ResultType
from .simple_types import JsonType

class CaseCollectionResultType(ResultType):
    def get_extension(self) -> str:
        return ".cases.json"

    def accepts_data(self, data) -> bool:
        from ....pipelines import CaseCollection
        if not isinstance(data, CaseCollection):
            return False
        return all(JsonType.is_json_compatible(c) for c in data.cases)

    def write(self, data, path: Path):
        cases = list(data.cases)
        JsonType().write(cases, path)

    def read(self, path: Path):
        from ....pipelines import CaseCollection
        cases = JsonType().read(path)
        return CaseCollection(cases)
