from .string_to_tags_parser import IStringToTagsParser
from enum import Enum

class ExactWordParser(IStringToTagsParser):
    def __init__(self,
                 field: str,
                 word_to_value: dict[str,object] | type[Enum],
                 ):
        self.field = field
        if isinstance(word_to_value, dict):
            self.word_to_value = {s.strip().lower(): v for s, v in word_to_value.items()}
        elif issubclass(word_to_value, Enum):
            self.word_to_value = {str(value): value for value in word_to_value}
        else:
            raise ValueError(f"`word_to_value` must be dict or Enum type, but was: {word_to_value}")

    def parse(self, text: str) -> list[dict]:
        s = text.lower().strip()
        for word, value in self.word_to_value.items():
            if s.startswith(word):
                return [{self.field: value}]
        raise ValueError(f"Cant find any of exact words `{','.join(self.word_to_value)}` in `{text}")

