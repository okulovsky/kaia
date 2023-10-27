from typing import *
from ...core import SetDub, IRandomizableDub
import num2words
from yo_fluq_ds import *
import numpy as np

class _IntDub(SetDub):

    def __init__(self,
                 name: str,
                 min: Optional[int] = None,
                 max: Optional[int] = None,
                 cardinal: bool = True,
                 ):
        self.min = min if min is not None else 1
        self.max = max if max is not None else 100
        self.ordinal = not cardinal
        super().__init__(list(range(self.min, self.max+1)), name)

    def _postprocess(self, s):
        return s.replace(',', '').replace('-',' ')

    def to_str(self, value) -> str:
        text = num2words.num2words(value, self.ordinal)
        text = self._postprocess(text)
        return text

    def to_all_strs(self, value) -> Tuple[str,...]:
        options = []
        options.append(self._postprocess(num2words.num2words(value, self.ordinal)))
        return tuple(options)








class CardinalDub(_IntDub):
    def __init__(self, min: Optional[int] = None, max: Optional[int] = None):
        super().__init__('CardinalDub', min, max, True)



class OrdinalDub(_IntDub):
    def __init__(self, min: Optional[int] = None, max: Optional[int] = None):
        super().__init__('OrdinalDub', min, max, False)


