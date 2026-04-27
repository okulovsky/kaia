import plotly.graph_objs as go


class LevelsHandler:
    def __init__(self):
        self.bar_times: list[float] = []
        self.bar_levels: list[float] = []
        self.threshold_times: list[float] = []
        self.threshold_values: list[float] = []

    def add(self, start_relative: float, end_relative: float, levels: list[float], silence_level: float):
        if len(levels) > 0:
            delta = (end_relative - start_relative) / len(levels)
            t = start_relative
            for level in levels:
                self.bar_times.append(t)
                self.bar_levels.append(level)
                t += delta
        if self.threshold_times:
            self.threshold_times.append(start_relative)
            self.threshold_values.append(self.threshold_values[-1])
        self.threshold_times.append(start_relative)
        self.threshold_values.append(silence_level)

    def get_traces(self) -> list:
        if self.threshold_times:
            self.threshold_times.append(0)
            self.threshold_values.append(self.threshold_values[-1])
        return [
            go.Bar(x=self.bar_times, y=self.bar_levels, name='Level'),
            go.Scatter(
                x=self.threshold_times,
                y=self.threshold_values,
                mode='lines',
                name='Threshold',
                line=dict(color='red', width=2, dash='dash'),
            ),
        ]