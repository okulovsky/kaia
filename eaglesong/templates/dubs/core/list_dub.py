from typing import Any, Iterable
from . import parser_intructions as PI
from .dub import IDub, DubParameters
from .template_dub import DictTemplateDub
from .iteration_dub import IterationDub


class ListDub(IDub):
    def __init__(self,
                 inner: IDub,
                 separator: str = ', ',
                 last_separator: str|None = ' and ',
                 word_if_empty: str|None = 'nothing',
                _type: type = tuple,
                ):
        self.last_separator = last_separator
        self.word_if_empty = word_if_empty
        self.separator = separator
        self.type = _type

        inside_template = IterationDub(
            DictTemplateDub(f"{separator}{inner.as_variable('inner')}"),
        )

        options = [
            f"{inner.as_variable('first')}{inside_template.as_variable('list')}",
        ]
        if last_separator is not None:
            options.append(
                f"{inner.as_variable('first')}{inside_template.as_variable('list')}{last_separator}{inner.as_variable('last')}"
            )
        if word_if_empty is not None:
            options.append(word_if_empty)

        self.inner_template = DictTemplateDub(*options)
        self.inner_dub = inner

    @staticmethod
    def compose_string(strings: list[str], separator: str, last_separator: str|None = None, word_if_empty:str|None = None):
        if len(strings) == 0:
            if word_if_empty is None:
                raise ValueError("This instance doesn't support empty sequences")
            else:
                return word_if_empty
        if last_separator is None:
            return separator.join(strings)
        if len(strings) == 1:
            return strings[0]
        return separator.join(strings[:-1])+last_separator+strings[-1]

    def _to_str_internal(self, value, parameters: DubParameters):
        vs = [self.inner_dub.to_str(v, parameters) for v in value]
        return ListDub.compose_string(vs, self.separator, self.last_separator, self.word_if_empty)


    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        return self.inner_template._get_parser_data_internal(variables_stack, parameters)

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        data = self.inner_template._convolute_values_internal(values, parameters)
        result = []
        if 'first' in data:
            result.append(data['first'])
        if 'list' in data:
            result.extend(z['inner'] for z in data['list'])
        if 'last' in data:
            result.append(data['last'])
        return self.type(result)

