from typing import *
from dataclasses import dataclass
import datetime

@dataclass
class HeatingInterval:
    begin: datetime.time
    end: datetime.time
    value: float

def number_to_time(n: float) -> datetime.time:
    hour = int(n)
    minutes = int((n-hour)*100)
    return datetime.time(hour, minutes)

@dataclass
class HeatingPlan:
    name: str
    default_temperature: float
    intervals: Tuple[HeatingInterval,...]

    def get_value_for(self, time: datetime.time):
        temperature = self.default_temperature
        for i in self.intervals:
            if time <= i.end and time >= i.begin:
                temperature = i.value
                break
        return temperature

    def create_experimental_variation(self):
        time = datetime.datetime(2022,1,1)
        intervals = []
        delta = 0
        for i in range(24*6-1):
            from_time = time.time()
            time += datetime.timedelta(minutes=10)
            temperature = self.get_value_for(from_time) + delta
            delta+=0.5
            if delta>1:
                delta=-1
            intervals.append(HeatingInterval(from_time, time.time(), temperature))
        return HeatingPlan('EXP '+self.name, self.default_temperature, tuple(intervals))





    @staticmethod
    def define(name: str,
               default_temperature: float,
               *intervals: Tuple[float, float, float]) -> 'HeatingPlan' :
        ints = tuple(HeatingInterval(
            number_to_time(i[0]),
            number_to_time(i[1]),
            i[2]) for i in intervals
        )
        return HeatingPlan(name, default_temperature, ints)


