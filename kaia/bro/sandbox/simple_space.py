from kaia.bro.core import ISpace, Slot, RangeInput, BoolInput, BroAlgorithm
from dataclasses import dataclass
from kaia.bro.amenities.basics import *
from kaia.bro.amenities.comm import *
import math

@dataclass(frozen=True)
class SimpleSpace(ISpace):
    int_slot: Slot[int] = Slot.field()
    string_slot: Slot[str] = Slot.field()

    def get_name(self):
        return 'simple'