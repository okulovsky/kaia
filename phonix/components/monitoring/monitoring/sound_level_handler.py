import plotly.graph_objs as go


class SoundLevelHandler:
    def __init__(self):
        # lists of relative times, levels and thresholds
        self.times: list[float] = []
        self.levels: list[float] = []

    def add(self, start_relative, end_relative, levels: list[float]):
        if len(levels) > 0:
            delta = (end_relative - start_relative)/len(levels)
            for item in levels:
                self.times.append(start_relative)
                self.levels.append(item)
                start_relative+=delta

    def get_traces(self) -> list[go.Bar]:
        return [
            go.Bar(
                x=self.times,
                y=self.levels,
                name='Level'
            ),
        ]