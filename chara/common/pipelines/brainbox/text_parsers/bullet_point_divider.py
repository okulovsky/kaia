class BulletPointDivider:
    DEFAULT_BULLET_POINTS = ('• ', '* ', '- ')

    def __init__(self, prefixes: tuple[str,...]|None = None):
        if prefixes is None:
            prefixes = BulletPointDivider.DEFAULT_BULLET_POINTS
        self.prefixes = prefixes

    def __call__(self, text: str) -> list[str]:
        result = []
        for line in text.split('\n'):
            for prefix in self.prefixes:
                if line.startswith(prefix):
                    result.append(line[len(prefix):])
                    break
        return result

