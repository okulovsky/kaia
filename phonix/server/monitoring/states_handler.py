import datetime
import plotly.graph_objs as go
from ...daemon import StateChange, MicState


class StatesHandler:
    def __init__(self):
        # prepare a buffer for each state
        self.state_buffers: dict[MicState, dict[str, list[float]]] = {
            s: {"xs": [], "ys": []}
            for s in MicState
        }

    def add(self, relative_time: float, last_level: float|None, item: StateChange):
        if last_level is None:
            return
        buf = self.state_buffers[item.state]
        buf["xs"].append(relative_time)
        buf["ys"].append(last_level)

    def get_traces(self) -> list[go.Scatter]:
        # define colors for each MicState
        state_color_map = {
            MicState.Standby:   'blue',
            MicState.Open:      'green',
            MicState.Recording: 'orange',
            MicState.Sending:   'purple',
        }

        traces: list[go.Scatter] = []
        for state, buf in self.state_buffers.items():
            xs = buf["xs"] or [None]
            ys = buf["ys"] or [None]
            traces.append(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode='markers',
                    name=state.name,
                    marker=dict(
                        size=12,
                        color=state_color_map.get(state, 'black'),
                        symbol='diamond'
                    ),
                    showlegend=True
                )
            )
        return traces
