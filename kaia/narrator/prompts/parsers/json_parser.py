import json
from .string_to_tags_parser import IStringToTagsParser

class ValueToTagParser(IStringToTagsParser):
    def __init__(self, field_name, parser):
        self.field_name = field_name
        self.parser = parser

    def parse(self, text: str):
        return [{self.field_name:  self.parser(text)}]


class PivotToTagParser(IStringToTagsParser):
    def __init__(self, parser):
        self.parser = parser

    def parse(self, text):
        js = self.parser(text)
        if not isinstance(js, dict):
            raise ValueError(f"Expected dict, but was {js}")
        return [js]



class JsonParser:
    def parse_text_only(self, text) -> str:
        buffer = []
        to_buffer = False
        for line in text.split('\n'):
            if line.strip().startswith('```'):
                to_buffer = not to_buffer
                continue
            if to_buffer:
                buffer.append(line)
        return '\n'.join(buffer)

    def parse(self, text: str) -> object:
        return json.loads(self.parse_text_only(text))

    def as_str(self, field_name):
        return ValueToTagParser(field_name, self.parse_text_only)

    def pivot(self):
        return PivotToTagParser(self.parse)

