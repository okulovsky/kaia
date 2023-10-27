from .interpreter import IAutomaton
from typing import *
from types import GeneratorType
from .primitives import Return, Terminate, AutomatonExit, Listen

class ContextRequest:
    pass


class Automaton(IAutomaton):
    def __init__(self,
                 function: Callable[[], Generator],
                 context: Any):
        self.function = function
        self.context = context
        self.generator = None #type: Optional[Generator]
        self._create_and_check_generator()

    def _create_and_check_generator(self):
        if not callable(self.function):
            raise ValueError(f'The function `{self.function}` is not callable.')
        try:
            generator = self.function()
        except Exception as ex:
            raise ValueError(f"Couldn't initialize generator {self.function}") from ex
        if not isinstance(generator, GeneratorType):
            raise ValueError(f'The result of `{self.function}()` is not a generator.'
                            'Have you forgotten `yield`?'
                            'If logic does not require it, just place `yield` without arguments at the first line of the function'
                             )
        return generator


    def process(self, item: Any):
        just_started = False
        if self.generator is None:
            self.generator = self._create_and_check_generator()
            just_started = True
        try:
            item_to_send = item
            while True:
                if just_started:
                    item_to_send = None
                    just_started = False
                returned_value = self.generator.send(item_to_send)
                if isinstance(returned_value, ContextRequest):
                    item_to_send = self.context
                elif returned_value is None:
                    item_to_send = item
                else:
                    return returned_value
        except StopIteration:
            self.generator = None
            return Return()
        except Return:
            self.generator = None
            return Return()
        except Terminate as terminate:
            self.generator = None
            return terminate





