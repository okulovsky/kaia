from dataclasses import dataclass
from datetime import datetime
from ..core import ISpace, Slot, BroAlgorithm, BroAlgorithmPresentation, RangeInput
from ..amenities import SettingsReader, SettingsHandler, Timer
from plotly import graph_objects as go


@dataclass(frozen=True)
class ControlSpace(ISpace):
    timestamp: Slot[datetime] = Slot.field()
    measurement: Slot[float] = Slot.field()
    high_value: Slot[float] = Slot.field(input = RangeInput(60,100))
    low_value: Slot[float] = Slot.field(input = RangeInput(20,70))
    state: Slot[bool] = Slot.field()
    debug: Slot[str] = Slot.field()

    def create_algorithm(self, measurement_change_per_minute):
        algorithm = BroAlgorithm(
            self,
            [
                SettingsReader(),
                SettingsHandler(self.high_value, value=80),
                SettingsHandler(self.low_value, value=50),
                Timer(self.timestamp, mock_time_delta_in_seconds=10),
                MockSensor(measurement_change_per_minute),
                control
            ],
            presentation=BroAlgorithmPresentation(
                plot,
            )
        )
        return algorithm


def plot(df):
    df = df.sort_values('timestamp').iloc[-1000:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.measurement))
    return fig




def get_state_duration(space: ControlSpace):
    last_change = (space
                   .history(space.timestamp, space.state)
                   .where(lambda z: z.state != space.state.last_value)
                   .select(lambda z: z.timestamp)
                   .first_or_default()
                   )
    if last_change is None:
        return None
    return (space.timestamp.last_value - last_change).total_seconds() / 3600


def control(space: ControlSpace):
    target_state = None
    if space.measurement.current_value > space.high_value.current_value:
        target_state = True
    if space.measurement.current_value < space.low_value.current_value:
        target_state = False

    space.debug.current_value = f'target: {target_state}. '

    if space.state.history.count() == 0:
        space.state.current_value = target_state if target_state is not None else False
        space.debug.current_value += 'First time'
        return

    if target_state is None:
        space.state.current_value = space.state.last_value
        space.debug.current_value += 'No change request'
        return

    delta = get_state_duration(space)
    space.debug.current_value += f'Timedelta {delta}'
    if delta is None or delta > 1:
        space.state.current_value = target_state
    else:
        space.state.current_value = space.state.last_value


class MockSensor:
    def __init__(self, measurement_change_per_minute):
        self.measurement_change_per_minute = measurement_change_per_minute

    def __call__(self, space: ControlSpace):
        if space.measurement.last_value is None:
            space.measurement.current_value = 50
            return
        time_delta = (space.timestamp.current_value - space.timestamp.last_value).total_seconds() / 60
        value_delta = self.measurement_change_per_minute * time_delta
        if space.state.last_value:
            value_delta = -value_delta
        space.measurement.current_value = space.measurement.last_value + value_delta



