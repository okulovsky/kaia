from ..brainbox import BrainBoxPipeline, TCase, TOption, BrainBoxCache
from brainbox import BrainBox
from brainbox.deciders import Ollama
from typing import Generic, Callable, Optional, Iterable


class LLMUnit(Generic[TCase, TOption]):
    def __init__(self,
                 model: str,
                 prompt_builder: Callable[[TCase], str],
                 parser_to_list: Optional[Callable[[str], list[TOption]]] = None,
                 parser_to_object: Optional[Callable[[str], TOption]] = None,
                 ):
        self.model = model
        self.prompt_builder = prompt_builder
        self.parser_to_list = parser_to_list
        self.parser_to_object = parser_to_object

        if (self.parser_to_list is not None) + (self.parser_to_object is not None) != 1:
            raise ValueError("You must provide exactly one of parser_to_list or parser_to_object.")


    def _task_builder(self, case: TCase):
        return BrainBox.Task.call(Ollama, self.model).question(self.prompt_builder(case))

    def _list_divider(self, s):
        return s

    def _merger(self, case, s):
        if self.parser_to_list is not None:
            return self.parser_to_list(s)
        else:
            return self.parser_to_object(s)


    def __call__(self, cache: BrainBoxCache[TCase, TOption], cases: Iterable[TCase]) -> None:
        unit = BrainBoxPipeline(
            self._task_builder,
            self._merger,
            self._list_divider if self.parser_to_list is not None else None,
        )
        unit.run(cache, cases)
