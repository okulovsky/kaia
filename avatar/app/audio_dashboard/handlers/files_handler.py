from dataclasses import dataclass

from ....daemon import SoundConfirmation

@dataclass
class FileDescription:
    group: str
    url: str
    begin: float
    end: float|None = None
    message_id: str|None = None

class FilesHandler:
    def __init__(self):
        self.files: list[FileDescription] = []

    def file_start(self, group: str, url: str, time: float, message_id: str|None = None) -> dict:
        self.files.append(FileDescription(group, url, time, message_id=message_id))

    def file_end_by_confirmation(self, confirmation: SoundConfirmation, relative_time: float):
        for file in self.files:
            if file.message_id is not None:
                if confirmation.is_confirmation_of(file.message_id):
                    file.end = relative_time
                    break

    def file_end_by_name(self, url: str, relative_time: float):
        for file in self.files:
            if file.url == url:
                file.end = relative_time
                break

    def get_shapes_and_annotations(self) -> tuple[list, list]:
        groups = list(dict.fromkeys(f.group for f in self.files))
        group_to_y = {g: i for i, g in enumerate(groups)}

        shapes = []
        annotations = []
        for f in self.files:
            y_center = group_to_y[f.group]
            x0 = f.begin
            x1 = f.end if f.end is not None else 0
            shapes.append(dict(
                type='rect',
                xref='x', yref='y',
                x0=x0, x1=x1,
                y0=y_center - 0.4, y1=y_center + 0.4,
                fillcolor='LightBlue',
                opacity=0.6,
                line_width=1,
                name=f.url,
            ))
            label = f.url.split('/')[-1]
            annotations.append(dict(
                x=(x0 + x1) / 2,
                y=float(y_center),
                text=label,
                xref='x', yref='y',
                showarrow=False,
                font=dict(size=9, color='black'),
            ))
        return shapes, annotations

