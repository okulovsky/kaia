from typing import *
from abc import ABC, abstractmethod
import numpy as np



class Dub(ABC):
    @abstractmethod
    def get_name(self):
        pass


class IRandomizableDub(ABC):
    @abstractmethod
    def get_random_value(self, random_state: Optional[np.random.RandomState] = np.random.RandomState()):
        pass

    def get_placeholder_value(self):
        return self.get_random_value()


