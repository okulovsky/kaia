import datetime
import plotly.graph_objs as go
from avatar.messaging import IMessage
from ....daemon import SoundLevelReport, MicStateChangeReport, SoundPlayStarted, SilenceLevelReport
from avatar.daemon import SoundConfirmation
from .sound_level_handler import SoundLevelHandler
from .silence_level_handler import SilenceLevelHandler
from .states_handler import StatesHandler
from .commands_handler import CommandsHandler
from plotly.subplots import make_subplots




class PhonixMonitoring:
    def __init__(self, data_generator, time_window: int = 50):
        self.data_generator = data_generator
        self.time_window = time_window
        self.data: list[IMessage] = []

    def get_figure(self):
        # 1) generate new items
        self.data_generator(self.data)
        now = datetime.datetime.now()
        recent = [
            item for item in self.data
            if (now - item.envelop.timestamp).total_seconds() < self.time_window
        ]
        recent.sort(key=lambda i: i.envelop.timestamp)
        self.data = recent
        return self.create_figure(self.data, now)

    def create_figure(self, data, now):
        # 3) instantiate handlers
        last_level = None
        levels = SoundLevelHandler()
        silence = SilenceLevelHandler()
        states = StatesHandler()
        commands = CommandsHandler()

        # 4) feed data into handlers
        for item in data:
            relative_time = (item.envelop.timestamp-now).total_seconds()
            if isinstance(item, SoundLevelReport):
                first_relative = (item.begin_timestamp - now).total_seconds()
                for record in item.levels:
                    levels.add(first_relative+record.delta, record.value)
            if isinstance(item, SilenceLevelReport):
                silence.add(relative_time, item.silence_level)
            elif isinstance(item, MicStateChangeReport):
                states.add(relative_time, item.state)
            elif isinstance(item, (SoundPlayStarted, SoundConfirmation)):
                commands.add(now, item)

        # 5) gather plot traces + command bars
        return self.build_plot(now, levels, silence, states, commands)

    def build_plot(self,
                   now: datetime.datetime,
                   levels: SoundLevelHandler,
                   silence: SilenceLevelHandler,
                   states: StatesHandler,
                   commands: CommandsHandler
                   ):
        traces = levels.get_traces() + silence.get_traces()
        c_shapes, c_annotations = commands.get_shapes_and_annotations(now)
        s_shapes, s_annotations = states.get_shapes_and_annotations()


        # 2) build a 2‑row subplot with shared X‑axis
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.15, 0.7, 0.15],
            vertical_spacing=0.02
        )

        for row in [1,2, 3]:
            fig.add_trace(
                go.Scatter(
                    x=[], y=[],  # <— no data at all
                    mode="none",  # <— completely invisible
                    showlegend=False
                ),
                row=row, col=1
            )

        for shape in s_shapes:
            shape = shape.copy()
            fig.add_shape(shape, row=1, col=1)

        for ann in s_annotations:
            ann = ann.copy()
            ann['yref'] = 'y1'
            fig.add_annotation(ann, row=1, col=1)


        # 3) add level/state traces into the top row
        for trace in traces:
            fig.add_trace(trace, row=2, col=1)



        # 4) copy each shape/annotation into the second row,
        #    by rebinding to yref='y2' (the second subplot's y‑axis)
        for shape in c_shapes:
            shape = shape.copy()
            fig.add_shape(shape, row=3, col=1)



        for ann in c_annotations:
            ann = ann.copy()
            ann['yref'] = 'y3'
            fig.add_annotation(ann, row=3, col=1)

        # Top plot: keep the same range, but hide its ticks & title
        for row in [1, 2]:
            fig.update_xaxes(
                range=[-self.time_window, 0],
                showticklabels=False,  # hide ticks on the top subplot
                row=row, col=1
            )

        fig.update_xaxes(
            range=[-self.time_window, 0],
            showticklabels=True,  # turn them back on for the bottom
            ticks='outside',
            title_text='Time (s)',  # give the bottom its title
            row=3, col=1
        )

        # style Y‑axes
        fig.update_yaxes(
            title_text='Input',
            row=2, col=1
        )

        for row in [1,3]:
            fig.update_yaxes(
                title_text='Output',
                showticklabels=False,
                row=row, col=1
            )
        # 6) final layout tweaks
        fig.update_layout(
            title='Phonix status',
            margin=dict(l=40, r=20, t=40, b=40),
            autosize=True
        )

        return fig

