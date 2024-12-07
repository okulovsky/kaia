from .string_to_tags_parser import IStringToTagsParser
from copy import deepcopy

class ProductBulletPointParser(IStringToTagsParser):
    def __init__(self, field: str, parser: 'BulletPointParser'):
        self.field = field
        self.parser = parser

    def parse(self, text: str) -> list[dict]:
        points = self.parser.parse(text)
        if len(points) == 0:
            raise ValueError('no bullet points found in\n'+text)
        return [{self.field:point} for point in points]



class AppendBulletPointParser(IStringToTagsParser):
    def __init__(self, field: str, parser: 'BulletPointParser'):
        self.field = field
        self.parser = parser

    def parse(self, text: str) -> list[dict]:
        points = self.parser.parse(text)
        if len(points) == 0:
            raise ValueError('no bullet points found in\n'+text)
        return [{self.field: ', '.join(points)}]



class BulletPointParser:
    DEFAULT_BULLET_POINTS = ('• ', '* ', '- ')

    def __init__(self, prefixes: tuple[str,...]|None = None):
        if prefixes is None:
            prefixes = BulletPointParser.DEFAULT_BULLET_POINTS
        self.prefixes = prefixes

    def parse(self, s: str):
        result = []
        for line in s.split('\n'):
            for prefix in self.prefixes:
                if line.startswith(prefix):
                    result.append(line[len(prefix):])
                    break
        return result

    def product_parser(self, field: str):
        return ProductBulletPointParser(field, self)

    def append_parser(self, field: str):
        return AppendBulletPointParser(field, self)
