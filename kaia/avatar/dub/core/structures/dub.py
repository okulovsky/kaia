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

    def get_placeholder_value(self):
        return self.get_random_value()


class ToStrDub(Dub, ABC):
    @abstractmethod
    def to_str(self, value):
        pass



class IdentityDub(ToStrDub):
    def to_str(self, value):
        return str(value)