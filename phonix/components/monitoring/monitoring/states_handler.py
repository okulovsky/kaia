import datetime
import plotly.graph_objs as go
from ....daemon import MicStateChangeReport, MicState


class StatesHandler:
    def __init__(self):
        self.shapes = []
        self.annotations = []
        self.last_state: MicState|None = None
        self.last_relative_time: float|None = None
        self.stat_to_color = {
            MicState.Standby: "Honeydew",
            MicState.Open: "LightSteelBlue",
            MicState.Recording: "MistyRose",

        }



    def add(self, relative_time: float, item: MicState):
        if self.last_state is not None and self.last_state in self.stat_to_color:
            self.shapes.append(dict(
                type="rect",
                xref="x",
                yref="paper",
                x0=self.last_relative_time,
                y0=0,
                x1=relative_time,
                y1=1,
                fillcolor=self.stat_to_color[self.last_state],
                opacity=0.5,
                line_width=0,
            ))

            self.annotations.append(dict(
                x=self.last_relative_time,
                y=1,  # верхний левый угол прямоугольника
                text=self.last_state.name,
                textangle=-90,
                xref="x", yref="paper",
                showarrow=False,
                font=dict(size=12, color="black"),
                xanchor="left",
                yanchor="top"
            ))

        self.last_relative_time = relative_time
        self.last_state = item


    def get_shapes_and_annotations(self) -> list[dict]:
        self.add(0, MicState.Standby)
        return self.shapes, self.annotations
