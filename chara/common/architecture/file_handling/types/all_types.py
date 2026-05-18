from .simple_types import *

def get_all_result_types():
    return [
        TextType(),
        PathType(),
        ParquetType(),
        JsonType(),
        PickleType(),
    ]