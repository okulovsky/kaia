from typing import *
from abc import ABC, abstractmethod
import numpy as np



class Dub:
    def get_name(self):
        return type(self).__name__


class IRandomizableDub(ABC):
    @abstractmethod
    def get_random_value(self, random_state: Optional[np.random.RandomState] = np.random.RandomState()):
        pass



class ToStrDub(Dub, ABC):
    def to_str(self, value):
        return str(value)

