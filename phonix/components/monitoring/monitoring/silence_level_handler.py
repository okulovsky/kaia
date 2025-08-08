import datetime
import plotly.graph_objs as go


class SilenceLevelHandler:
    def __init__(self):
        # lists of relative times, levels and thresholds
        self.times: list[float] = []
        self.thresholds: list[float] = []

    def add(self, relative_time: float, value: float):
        # compute seconds‐ago
        if len(self.times) > 0:
            self.times.append(relative_time)
            self.thresholds.append(self.thresholds[-1])
        self.times.append(relative_time)
        self.thresholds.append(value)

    def get_traces(self) -> list[go.Scatter]:
        self.times.append(0)
        if len(self.thresholds) != 0:
            self.thresholds.append(self.thresholds[-1])
        return [
            go.Scatter(
                x=self.times,
                y=self.thresholds,
                mode='lines',
                name='Threshold',
                line=dict(color='red', width=2, dash='dash')
            )
        ]