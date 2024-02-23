import copy
from typing import *
from yo_fluq_ds import Queryable, Query
from enum import Enum
from .slot_input import SlotInput
from dataclasses import field

TType = TypeVar('TType')

class Tracker:
    class Action(Enum):
        read_last = 0
        read_current = 1
        read_history = 2
        read_all = 3
        write = 100


    class Record:
        def __init__(self, action: 'Tracker.Action', slot_name: str, value: Any, unit: Optional[str]):
            self.action = action
            self.slot_name = slot_name
            self.value = value
            self.unit = unit

    def __init__(self):
        self.log = [] #type: List[Tracker.Record]
        self.unit = None #type: Optional[str]


    def register(self, action: 'Tracker.Action', slot: 'Slot', value: Any):
        self.log.append(Tracker.Record(action, slot.name, value, self.unit))








class Slot(Generic[TType]):
    @staticmethod
    def field(
            *args,
            stored: bool = True,
            shown: bool = True,
            input: Optional[SlotInput] = None,
            hint: str = None):
        if len(args)>0:
            raise ValueError('Only key-value arguments are allowed')
        def _factory():
            return Slot(stored=stored,
                        shown = shown,
                        input = copy.deepcopy(input),
                        hint = hint)
        return field(default_factory=_factory)

    @staticmethod
    def slotname(value: Union[str, 'Slot', None]):
        return value.name if isinstance(value, Slot) else value

    def __init__(self,
                 *args,
                 stored: bool = True,
                 shown: bool = True,
                 input: Optional[SlotInput] = None,
                 hint: str = None):
        if len(args)>0:
            raise ValueError('Only key-value arguments are allowed')
        self.shown = shown
        self.stored = stored
        self.input = input
        self.hint = hint

        self._history = [] #type: List[TType]
        self._current_value = None #type: Optional[TType]
        self._tracker = None #type: Optional[Tracker]

        self._name = None

    @property
    def name(self):
        return self._name

    def length(self):
        return len(self._history)

    @property
    def last_value(self) -> Optional[TType]:
        value = None
        if len(self._history) > 0:
            value = self._history[0]
        if self._tracker is not None:
            self._tracker.register(Tracker.Action.read_last, self, value)
        return value


    @property
    def current_value(self) -> TType:
        if self._tracker is not None:
            self._tracker.register(Tracker.Action.read_current, self, self._current_value)
        return self._current_value

    @current_value.setter
    def current_value(self, value: TType):
        if self._tracker is not None:
            self._tracker.register(Tracker.Action.write, self, value)
        self._current_value = value

    @property
    def history(self) -> Queryable[TType]:
        if self._tracker is not None:
            self._tracker.register(Tracker.Action.read_history, self, None)
        return Query.en(self._history)

    @property
    def history_with_current(self) -> Queryable[TType]:
        if self._tracker is not None:
            self._tracker.register(Tracker.Action.read_all, self, None)
        return Query.en([self._current_value]+self._history)

    def __repr__(self):
        return f"Slot('{self.name}')"




