import gradio
from .label_annotator import LabelAnnotator, LabelAnnotatorSettings, ITaskPlanner
from ..core import TCase
from typing import Generic, Callable

class TextLabelAnnotator(Generic[TCase], LabelAnnotator[TCase]):
    def __init__(self,
                 case_to_text: Callable[[TCase], str],
                 settings: LabelAnnotatorSettings,
                 planer: ITaskPlanner|None = None,
                 mock_annotation: Callable[[TCase], str] = None
                 ):
        self.case_to_text = case_to_text
        self._text_box: gradio.Label | None = None
        super().__init__(settings, planer, mock_annotation)

    def create_inner_interface(self) -> list:
        self._text_box = gradio.Label()
        return [self._text_box]

    def inner_controls_command(self, id: str) -> dict:
        case = next(c for c in self.cases if c.get_id()==id)
        return {self._text_box: self.case_to_text(case)}

