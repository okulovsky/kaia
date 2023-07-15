from typing import *
from kaia.bro.core import Slot, ISpace
from kaia.bro import amenities as am
from dataclasses import dataclass
from queue import Queue
import numpy as np

@dataclass(frozen=True)
class Space(ISpace):
    readings: Slot[List[int]] = Slot.field()
    avg_readings: Slot[float] = Slot.field()
    stable_weight: Slot[int] = Slot.field()
    new_stable_weight: Slot[int] = Slot.field()

    def get_name(self):
        return 'scales'


class ScalesReader:
    def __init__(self, reader_runner: Callable[[Queue], None]):
        self.reader_runner = reader_runner
        self.queue = None

    def __call__(self, space: Space):
        if self.queue is None:
            self.queue = Queue()
            self.reader_runner(self.queue)
        result = []
        while not self.queue.empty():
            result.append(self.queue.get())
        space.readings.current_value = tuple(result)


class ReadingsAverager:
    def __call__(self, space: Space):
        if space.readings.current_value is None or len(space.readings.current_value)==0:
            return
        space.avg_readings.current_value = np.mean(space.readings.current_value)


class ScalesStabilizer:
    def __init__(self, allowed_variance = 5, history_length = 10):
        self.allowed_variance = allowed_variance
        self.history_length = history_length


    def __call__(self, space: Space):
        empty = space.readings.history_with_current.take_while(lambda z: len(z)==0).take(self.history_length).count()
        if empty >= self.history_length:
            return
        history = space.readings.history_with_current.where(lambda z: z is not None).select_many(lambda z: reversed(z)).take(self.history_length).to_list()
        if len(history)<self.history_length:
            return
        if space.stable_weight.last_value is None:
            last = history[-1]
        else:
            last = space.stable_weight.last_value
        value_is_ok = True
        for h in history:
            if abs(h-last)>5:
                value_is_ok = False
                break
        if value_is_ok:
            space.stable_weight.current_value = last
        else:
            space.stable_weight.current_value = None





if __name__ == '__main__':
    from zoo.smart_home.scales.smart_lab_scales import SmartLabReaderConverter
    from kaia.bro.core import BroServer, BroAlgorithm
    from kaia.bro.amenities import PrintReporter
    from kaia.infra.comm import Sql

    space = Space()
    algorithm = BroAlgorithm(
        space,
        [
            ScalesReader(SmartLabReaderConverter.run),
            ReadingsAverager(),
            ScalesStabilizer(history_length=5),
            am.ChangeDetector(space.stable_weight, space.new_stable_weight),
            PrintReporter(),
        ],
        update_interval_in_millisecods=0,
        keep_track_in_storage=True
    )
    conn = Sql.file('sample', True)
    storage = conn.storage()
    messenger = conn.messenger()
    server = BroServer([algorithm], storage, messenger, pause_in_milliseconds=1000, iterations_limit=60)
    server.run()

