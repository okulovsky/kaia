from .dub_binding import DubBinding
from .set_dub import DictDub


class DictBinding(DubBinding):
    def __init__(self, field: str, dictionary: dict):
        super().__init__(
            DictDub(dictionary),
            field,
            False,
            True,
            None
        )