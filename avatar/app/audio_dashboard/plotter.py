import datetime
import plotly.graph_objs as go


def _naive(dt: datetime.datetime) -> datetime.datetime:
    """Convert timezone-aware UTC timestamps to naive local time for comparison with datetime.now()."""
    return dt.astimezone().replace(tzinfo=None) if dt.tzinfo is not None else dt

from ...daemon import (
    SoundLevelReport, StatefulRecorderStateEvent,
    SoundCommand, SoundConfirmation, SystemSoundCommand,
    SoundStartEvent, SoundEvent,
)
from .handlers import LevelsHandler, StatesHandler, FilesHandler
from plotly.subplots import make_subplots
from .data_reader import DataReader


class Plotter:
    def __init__(self, reader: DataReader):
        self.reader = reader

    def get_figure(self):
        self.reader.update_data()
        return self.create_figure(self.reader.events, self.reader.last_update)

    def create_figure(self, data, now):
        levels = LevelsHandler()
        states = StatesHandler()
        files = FilesHandler()

        for item in data:
            relative_time = (item.envelop.timestamp - now).total_seconds()
            if isinstance(item, SoundLevelReport):
                start_relative = (_naive(item.begin_timestamp) - now).total_seconds()
                end_relative = (_naive(item.end_timestamp) - now).total_seconds()
                levels.add(start_relative, end_relative, item.levels, item.silence_level)
            elif isinstance(item, StatefulRecorderStateEvent):
                states.add(relative_time, item.state)
            elif isinstance(item, SystemSoundCommand):
                files.file_start('system', f'/frontend/system_sounds/{item.sound_name}.wav', relative_time, item.envelop.id)
            elif isinstance(item, SoundCommand):
                files.file_start('output', f'/cache/{item.file_id}', relative_time, item.envelop.id)
            elif isinstance(item, SoundConfirmation):
                files.file_end_by_confirmation(item, relative_time)
            elif isinstance(item, SoundStartEvent):
                files.file_start('input', f'/cache/{item.file_id}', relative_time)
            elif isinstance(item, SoundEvent):
                files.file_end_by_name(f'/cache/{item.file_id}', relative_time)

        return self.build_plot(levels, states, files)

    def build_plot(self, levels: LevelsHandler, states: StatesHandler, files: FilesHandler):
        time_window = self.reader.past_span_in_seconds

        level_traces = levels.get_traces()
        state_shapes, state_annotations = states.get_shapes_and_annotations()
        file_shapes, file_annotations = files.get_shapes_and_annotations()

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.15, 0.7, 0.15],
            vertical_spacing=0.02,
        )

        # Invisible anchor traces to pin the x-axis range per row
        for row in [1, 2, 3]:
            fig.add_trace(
                go.Scatter(x=[], y=[], mode='markers', showlegend=False),
                row=row, col=1,
            )

        # Row 1: recorder states (background coloured rectangles)
        for shape in state_shapes:
            fig.add_shape(shape, row=1, col=1)
        for ann in state_annotations:
            ann = ann.copy()
            ann['yref'] = 'y1'
            fig.add_annotation(ann)

        # Row 2: sound levels (bar chart + silence threshold line)
        for trace in level_traces:
            fig.add_trace(trace, row=2, col=1)

        # Row 3: file playback (rectangles per group)
        for shape in file_shapes:
            fig.add_shape(shape, row=3, col=1)
        for ann in file_annotations:
            ann = ann.copy()
            fig.add_annotation(ann, row=3, col=1)

        for row in [1, 2]:
            fig.update_xaxes(range=[-time_window, 0], showticklabels=False, row=row, col=1)
        fig.update_xaxes(
            range=[-time_window, 0],
            showticklabels=True,
            ticks='outside',
            title_text='Time (s)',
            row=3, col=1,
        )

        fig.update_yaxes(title_text='State', showticklabels=False, row=1, col=1)
        fig.update_yaxes(title_text='Level', row=2, col=1)
        fig.update_yaxes(title_text='Output', row=3, col=1)

        fig.update_layout(
            title='Audio dashboard',
            margin=dict(l=40, r=20, t=40, b=40),
            autosize=True,
        )

        return fig
