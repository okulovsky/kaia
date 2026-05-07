from pathlib import Path
import gradio
from .label_annotator import LabelAnnotator, LabelAnnotatorSettings, ITaskPlanner
from ..core import TCase
from typing import Generic, Callable


class AudioLabelAnnotator(Generic[TCase], LabelAnnotator[TCase]):
    def __init__(self,
                 case_to_file: Callable[[TCase], Path],
                 settings: LabelAnnotatorSettings,
                 planer: ITaskPlanner | None = None,
                 mock_annotation: Callable[[TCase], str] = None,
                 ):
        self.case_to_file = case_to_file
        self._audio: gradio.Audio | None = None
        super().__init__(settings, planer, mock_annotation)

    def create_inner_interface(self) -> list:
        self._audio = gradio.Audio(autoplay=True)
        return [self._audio]

    def inner_controls_command(self, id: str) -> dict:
        case = next(c for c in self.cases if c.get_id() == id)
        return {self._audio: gradio.update(value=str(self.case_to_file(case)), autoplay=True)}
