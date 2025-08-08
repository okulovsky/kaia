import plotly.graph_objs as go


class SoundLevelHandler:
    def __init__(self):
        # lists of relative times, levels and thresholds
        self.times: list[float] = []
        self.levels: list[float] = []

    def add(self, relative_time: float, level: float):
        # compute seconds‐ago
        self.times.append(relative_time)
        self.levels.append(level)

    def get_traces(self) -> list[go.Bar]:
        return [
            go.Bar(
                x=self.times,
                y=self.levels,
                name='Level'
            ),
        ]