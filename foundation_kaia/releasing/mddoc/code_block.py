from .doc_block import IDockBlock, strip_common_indent

class CodeBlock(IDockBlock):
    def __init__(self, lines: list[str]):
        self.lines = lines

    def get_lines(self) -> list[str]:
        return self.lines

    def to_md(self) -> str:
        result = strip_common_indent(self.lines)
        if not result:
            return ''
        return '```python\n' + '\n'.join(result) + '\n```'