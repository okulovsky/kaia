import datetime
import plotly.graph_objs as go
from ...daemon import SoundLevel

class SoundLevelHandler:
    def __init__(self):
        # lists of relative times, levels and thresholds
        self.times: list[float] = []
        self.levels: list[float] = []

    def add(self, relative_time: float, item: SoundLevel):
        # compute seconds‐ago
        self.times.append(relative_time)
        self.levels.append(item.level)

    def get_traces(self) -> list[go.Scatter]:
        return [
            go.Scatter(
                x=self.times,
                y=self.levels,
                mode='lines+markers',
                name='Level'
            ),
        ]