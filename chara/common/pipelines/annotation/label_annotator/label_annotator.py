import gradio as gr
from abc import abstractmethod
from typing import Any
from ..core import IGradioAnnotator, ITaskPlanner, SimpleTaskPlanner
from dataclasses import dataclass
from .annotation_cache import LabelAnnotationCache

@dataclass
class LabelAnnotatorSettings:
    labels: tuple[str,...]
    skip_button: str|None = None

    def get_all_names(self) -> tuple[str,...]:
        if self.skip_button is not None:
            return self.labels+(self.skip_button,)
        return self.labels


class LabelAnnotator(IGradioAnnotator[LabelAnnotationCache]):
    Settings = LabelAnnotatorSettings

    def __init__(self,
                 settings: LabelAnnotatorSettings,
                 task_planner: ITaskPlanner|None,
                 ):
        self.settings = settings
        self.task_planner = task_planner if task_planner is not None else SimpleTaskPlanner()

        self._progress: gr.Slider | None = None
        self._summary: gr.Slider | None = None
        self._undo_button: gr.Button | None = None
        self._all_done: gr.Label|None = None
        self._inner_controls: list | None = None
        self._buttons: list[gr.Button] | None = None

        self.last_id: str | None = None

    @abstractmethod
    def get_tasks(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def create_inner_interface(self) -> list:
        ...

    @abstractmethod
    def inner_controls_command(self, id: str) -> dict:
        ...

    def create_interface(self) -> gr.Blocks:
        self.task_planner.setup(self.cache, self.get_tasks())
        with gr.Blocks() as interface:
            with gr.Row():
                self._progress = gr.Slider()
                self._summary = gr.Label()
                self._undo_button = gr.Button("Undo")
            self._all_done = gr.Label(visible=False)

            self._inner_controls = self.create_inner_interface()


            with gr.Row():
                buttons = []
                for button_name in self.settings.get_all_names():
                    button = gr.Button(button_name)
                    buttons.append(button)
                self._buttons = buttons

            all_controls = [self._progress, self._summary, self._undo_button, self._all_done] + self._inner_controls + self._buttons

            self._undo_button.click(self._on_undo_button, outputs=all_controls, api_name='on_undo')
            interface.load(self._on_load, outputs=all_controls, api_name='on_load')
            for button, button_name in zip(self._buttons, self.settings.get_all_names()):
                button.click(
                    self._on_button,
                    inputs=[button],
                    outputs=all_controls,
                    api_name="on_button"
                )
        return interface

    def _final_state(self):
        tasks_count = len(self.get_tasks())
        summary = self.cache.get_summary()
        result = {
            self._progress: gr.update(
                minimum=0,
                maximum=tasks_count,
                value=tasks_count,
                interactive=False),
            self._summary: summary,
            self._undo_button: gr.update(interactive=False),
            self._all_done: gr.update(visible=True, value='ALL DONE')
        }
        for button in self._buttons:
            result[button] = gr.update(visible=False)
        for control in self._inner_controls:
            result[control] = gr.update(visible=False)
        return result


    def _get_state(self):
        self.last_id = self.task_planner.get_next()
        if self.last_id is None:
            self.cache.finish_annotation()
            return self._final_state()

        summary = self.cache.get_summary()
        annotated_count = sum(status.annotated for status in self.cache.get_annotation_status().values())
        tasks_count = len(self.get_tasks())
        result = {
            self._progress: gr.update(
                minimum=0,
                maximum=tasks_count,
                value=annotated_count,
                interactive=False),
            self._summary: summary,
            self._undo_button: gr.update(interactive=annotated_count>0),
            self._all_done: gr.update(visible=False)
        }
        result.update(self.inner_controls_command(self.last_id))
        return result

    def _on_undo_button(self):
        self.cache.undo()
        return self._get_state()

    def _on_load(self):
        return self._get_state()

    def _on_button(self, button: str):
        if self.last_id is None:
            raise ValueError("Cannot process button, no current sample is available")
        if button == self.settings.skip_button:
            self.cache.skip(self.last_id)
        else:
            self.cache.add(self.last_id, button)
        self.last_id = None
        return self._get_state()


    def mock_annotation(self, cache: LabelAnnotationCache):
        ptr = 0
        self.task_planner.setup(cache, self.get_tasks())
        while True:
            next_id = self.task_planner.get_next()
            if next_id is None:
                break
            cache.add(next_id, self.settings.labels[ptr])
            ptr = (ptr+1) % len(self.settings.labels)








