from .doc_block import IDockBlock

class CodeBlock(IDockBlock):
    def __init__(self, lines: list[str]):
        self.lines = lines

    def get_lines(self) -> list[str]:
        return self.lines

    def to_md(self) -> str:
        non_empty = [l for l in self.lines if l.strip() != '']
        if not non_empty:
            return ''
        min_indent = min(len(l) - len(l.lstrip()) for l in non_empty)
        result = []
        for line in self.lines:
            result.append('' if line.strip() == '' else line[min_indent:])
        while result and result[0] == '':
            result.pop(0)
        while result and result[-1] == '':
            result.pop()
        return '```python\n' + '\n'.join(result) + '\n```'