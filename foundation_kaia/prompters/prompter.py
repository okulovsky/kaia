from .abstract_prompter import IPrompter, T, Generic
from .address import Address
from .template_parts import ITemplatePart, ConstantTemplatePart
import re

class Parser:
    def __init__(self):
        self.parts = []

    def parse_next(self, part: str):
        if part.startswith('<<') and part.endswith('>>'):
            uid = part[2:-2]
            token = ITemplatePart.parse_gc(uid)
            self.parts.append(token)
        else:
            if part != '':
                self.parts.append(ConstantTemplatePart(part))

    def finalize(self):
        return tuple(self.parts)



def _parse(template: str) -> tuple[ITemplatePart,...]:
    parser = Parser()
    parts = re.split('(<<[^>]+>>)', template)
    for p in parts:
        parser.parse_next(p)
    return parser.finalize()


class Prompter(IPrompter[T], Generic[T]):
    def __init__(self, template: str|tuple[ITemplatePart,...]):
        if isinstance(template, str):
            self.template = _parse(template)
        else:
            self.template = template

    def __call__(self, obj: T) -> str:
        return ''.join(part.to_str(obj) for part in self.template)

    def to_readable_string(self):
        return ''.join(p.to_readable_expression() for p in self.template)

