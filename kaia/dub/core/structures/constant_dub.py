from typing import *
from .dub import ToStrDub
import numpy as np

class ConstantDub(ToStrDub):
    def __init__(self, value: str):
        self.value = value

    def _get_random_value_internal(self, random_state: np.random.RandomState) -> str:
        return self.value

    def to_str(self, value: str) -> str:
        return self.value

    def get_name(self):
        return f'[Constant]: {self.value}'
