from .step import LLMRequestStep
from typing import Callable, Any

class CustomParse(LLMRequestStep):
    def __init__(self,
                 parser: Callable[[Any, str], Any]|None = None,
                 divider: Callable[[str], list]|None = None,
                 ):
        self.parser = parser
        self.divider = divider

    def get_parser(self) -> Callable[[Any, str], Any]|None:
        return self.parser

    def get_divider(self) -> Callable[[str], list]|None:
        return self.divider
