from .parser import IParser

class _JointParser(IParser[str]):
    def __init__(self, inner_parser: 'BulletPointParser', join_by: str = ', '):
        self.inner_parser = inner_parser
        self.join_by = join_by

    def __call__(self, text: str) -> str:
        return self.join_by.join(self.inner_parser(text))


class BulletPointParser(IParser[list[str]]):
    DEFAULT_BULLET_POINTS = ('• ', '* ', '- ')

    def __init__(self,
                 join: str|None = None,
                 prefixes: tuple[str,...]|None = None
                 ):
        self.join = join
        if prefixes is None:
            prefixes = BulletPointParser.DEFAULT_BULLET_POINTS
        self.prefixes = prefixes

    def __call__(self, text: str):
        result = []
        for line in text.split('\n'):
            for prefix in self.prefixes:
                if line.startswith(prefix):
                    result.append(line[len(prefix):])
                    break
        return result

    def joint(self, by: str =', '):
        return _JointParser(self, by)
