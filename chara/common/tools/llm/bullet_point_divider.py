class BulletPointDivider:
    DEFAULT_BULLET_POINTS = ('• ', '* ', '- ')
    DEFAULT_EXCLUDE_SYMBOLS = ("'", '*', '"')

    def __init__(self, prefixes: tuple[str,...]|None = None, exclude_symbols: tuple[str,...]|None = None):
        if prefixes is None:
            prefixes = BulletPointDivider.DEFAULT_BULLET_POINTS
        self.prefixes = prefixes

        if exclude_symbols is None:
            exclude_symbols =  BulletPointDivider.DEFAULT_EXCLUDE_SYMBOLS
        self.exclude_symbols = exclude_symbols

    def clean_option(self, s: str):
        while s[0] in self.exclude_symbols:
            s = s[1:]
        while s[-1] in self.exclude_symbols:
            s = s[:-1]
        return s

    def __call__(self, text: str) -> list[str]:
        result = []
        for line in text.split('\n'):
            for prefix in self.prefixes:
                if line.startswith(prefix):
                    result.append(self.clean_option(line[len(prefix):]))
                    break
        return result