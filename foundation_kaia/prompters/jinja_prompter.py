from jinja2 import Template, Environment, meta
from typing import Generic
from .abstract_prompter import IPrompter, T
from dataclasses import is_dataclass
from copy import copy
import re
class JinjaPrompter(IPrompter, Generic[T]):
    def __init__(self, template: str, prettify_newlines: bool = True):
        self._template_text = template.replace('<<', '{{').replace('>>', '}}')
        self._template = Template(self._template_text)
        self._prettify_newlines = prettify_newlines

    @staticmethod
    def normalize_newlines(text: str) -> str:
        text = re.sub(r'\n{2,}', '\n\n', text)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        return text

    def get_variables(self):
        env = Environment()
        parsed_content = env.parse(self._template_text)
        variables = meta.find_undeclared_variables(parsed_content)
        return variables

    def __call__(self, obj: T) -> str:
        values = {}
        if is_dataclass(obj):
            if isinstance(obj, type):
                pass
            else:
                values = copy(obj.__dict__)
        elif isinstance(obj, dict):
            values = copy(obj)
        values['_'] = obj

        s = self._template.render(**values)

        if self._prettify_newlines:
            s = JinjaPrompter.normalize_newlines(s)

        return s


