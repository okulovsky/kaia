from .simple_types import *
from .case_collection_type import CaseCollectionResultType

def get_all_result_types():
    return [
        TextType(),
        PathType(),
        ParquetType(),
        CaseCollectionResultType(),
        JsonType(),
        PickleType(),
    ]