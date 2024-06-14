from typing import *
from ...core import IDecider

class OutputTranslator(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self,
                 input,
                 take_array_element: Optional[int] = None
                 ):
        result = input
        if take_array_element is not None:
            result = result[take_array_element]
        return result


