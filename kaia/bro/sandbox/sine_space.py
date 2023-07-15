from plotly import graph_objects as go
from ..core import ISpace, Slot, RangeInput, BoolInput, BroAlgorithm, BroAlgorithmPresentation
from dataclasses import dataclass
from ..amenities.basics import *
from ..amenities.comm import *
import math


def _custom_validator(value):
    return 'Too low' if value<1 else True


@dataclass(frozen=True)
class SinSpace(ISpace):
    time: Slot[float] = Slot.field()
    amplitude: Slot[float] = Slot.field(input = RangeInput(0, 10))
    frequency: Slot[float] = Slot.field(input = RangeInput(0, 10, custom_validator=_custom_validator ))
    signal: Slot[float] = Slot.field()
    cosine: Slot[bool] = Slot.field(input = BoolInput())

    def get_name(self):
        return 'sin'

    def create_algorithm(self):
        return BroAlgorithm(
            self,
            [
                SettingsReader(),
                SettingsHandler(self.amplitude, 1),
                SettingsHandler(self.frequency, 1),
                SettingsHandler(self.cosine, False),
                Incrementer(self.time, 0, 0.1),
                sin_algorithm
            ],
            1000,
            presentation=BroAlgorithmPresentation(
                plot_function=plot,
                data_update_in_milliseconds=1000,
                plot_update_in_milliseconds=1000)
        )

def sin_algorithm(space: SinSpace):
    if space.cosine.current_value:
        f = math.cos
    else:
        f = math.sin
    space.signal.current_value = f(space.frequency.current_value*space.time.current_value)*space.amplitude.current_value


def plot(df):
    df = df.sort_values('time').iloc[-100:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.time, y=df.signal))
    return fig
