from typing import *
from .space import TSpace
from .slot import Slot, Tracker
from .unit import IUnit, GenericUnit
from ...infra.comm import IStorage, IMessenger, MessengerQuery
import pandas as pd

class BroAlgorithmPresentation:
    def __init__(self,
                 plot_function: Optional[Callable[[pd.DataFrame], Any]] = None,
                 data_update_in_milliseconds: Optional[int] = 1000,
                 plot_update_in_milliseconds: Optional[int] = 10000
                 ):
        self.plot_function = plot_function
        self.data_update_in_milliseconds = data_update_in_milliseconds
        self.plot_update_in_milliseconds = plot_update_in_milliseconds



class BroAlgorithm:
    def __init__(self,
                 space: TSpace,
                 units: List[Union[Callable[[TSpace], None], IUnit]],
                 min_history_length: Optional[int] = None,
                 max_history_length: Optional[int] = None,
                 update_interval_in_millisecods: int = 0,
                 keep_track_in_storage: bool = False,
                 presentation: Optional[BroAlgorithmPresentation] = None
                 ):
        self.space = space
        self.units = [GenericUnit(u) for u in units]
        self.min_history_length = min_history_length
        if self.min_history_length is not None:
            self.max_history_length = max_history_length if max_history_length is not None else self.min_history_length * 2
        else:
            self.max_history_length = None
        self.update_interval_in_milliseconds = update_interval_in_millisecods
        self.keep_track_in_storage = keep_track_in_storage
        self.presentation = presentation
        if self.presentation is None:
            self.presentation = BroAlgorithmPresentation()

    def start_up(self, storage: IStorage, messenger: IMessenger):
        self.space.restore_from_storage(storage, self.min_history_length)

    def iterate(self,
                storage: IStorage,
                messenger: IMessenger,
                ):
        tracker = Tracker()
        slots = list(self.space.get_slots())
        for slot in self.space.get_slots():
            slot._current_value = None
            slot._tracker = tracker


        #running units
        for unit in self.units:
            tracker.unit = unit.get_name()
            unit.run(self.space, messenger)

        #stopping recorder
        for slot in slots:
            slot._tracker = None

        #moving values from current in history
        for slot in slots:
            slot._history.insert(0, slot.current_value)
            if self.min_history_length is not None:
                if len(slot._history) > self.max_history_length:
                    slot._history = slot._history[:self.min_history_length]
            slot._current_value = None


        #dumping in the logs
        if self.space.is_loggable():
            values = self.space.as_dict()
            if self.keep_track_in_storage:
                values['@log'] = tracker.log
            for slot in self.space.get_slots():
                if not slot.stored:
                    values[slot.name] = None
            storage.save(self.space.get_name(), values)





