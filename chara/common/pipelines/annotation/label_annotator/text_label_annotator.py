import gradio

from .label_annotator import LabelAnnotator, LabelAnnotatorSettings, ITaskPlanner

class TextLabelAnnotator(LabelAnnotator):
    def __init__(self, tasks: dict[str, str], settings: LabelAnnotatorSettings, planer: ITaskPlanner|None = None):
        self.tasks = tasks
        self._text_box: gradio.Label | None = None
        super().__init__(settings, planer)

    def get_tasks(self) -> dict[str, str]:
        return self.tasks

    def create_inner_interface(self) -> list:
        self._text_box = gradio.Label()
        return [self._text_box]

    def inner_controls_command(self, id: str) -> dict:
        return {self._text_box: self.tasks[id]}

