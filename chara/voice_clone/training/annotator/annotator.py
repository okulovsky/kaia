from ....tools.base_annotator import BaseAnnotator
from pathlib import Path
import numpy as np
from .data import Data
import gradio as gr
from ..exporters import IExporter
from kaia.common import Loc
from yo_fluq import *

class Annotator(BaseAnnotator):
    class Feedback:
        yes = 'Yes'
        bad_sentence = 'Bad sentence'
        skip = 'Skip'

    Data = Data

    def __init__(self,
                 path: Path,
                 data: Data,
                 exporter: IExporter,
                 button_captions: tuple[str,...],
                 randomize: bool = True
                 ):
        super().__init__(path)
        self.data = data
        self.exporter = exporter
        self.current_voice = None
        self.button_captions = button_captions
        self.randomize = randomize

    def on_feedback(self, id: str, feedback: str):
        if id not in self.data.file_to_data:
            return
        if feedback == Annotator.Feedback.skip:
            return
        self.data.solved_files.add(id)
        item = self.data.file_to_data[id]
        if feedback == Annotator.Feedback.yes:
            self.data.solved_texts.add((item.character, item.text))
            self.data.voice_to_duration[item.character] += item.duration
        if feedback == Annotator.Feedback.bad_sentence:
            self.data.bad_sentences.add(item.text)

    def get_next(self) -> BaseAnnotator.Sample:
        if self.current_voice is None:
            return BaseAnnotator.Sample(
                None,
                {
                    self.progress_control: 0,
                    self.text_control: "Select a voice",
                    self.audio_control: None,
                    self.file_id_control: '',
                    self.total_duration: '',
                })
        allowed, total = self.data.get_available(self.current_voice)
        progress_update = gr.update(maximum=total, value=total - len(allowed))
        dutation = str(self.data.voice_to_duration.get(self.current_voice,0))
        if len(allowed) == 0:
            return BaseAnnotator.Sample(
                None,
                {
                    self.progress_control: progress_update,
                    self.text_control: "ALL DONE!",
                    self.audio_control: None,
                    self.file_id_control: '',
                    self.total_duration: dutation
                }
            )
        if self.randomize:
            idx = int(np.random.randint(len(allowed)))
        else:
            idx = 0
        item = allowed[idx]
        content = self.exporter.get_content(item)
        path = Loc.data_folder/'audio_annotator_temp_file.wav'
        FileIO.write_bytes(content, path)
        return BaseAnnotator.Sample(
            item.filename,
            {
                self.progress_control: progress_update,
                self.text_control: item.text,
                self.audio_control: path,
                self.file_id_control: item.filename,
                self.total_duration: dutation
            }
        )

    def cm_voice_change(self, voice):
        self.current_voice = voice

    def create_interface(self):
        with gr.Blocks() as demo:
            select_voice = gr.Dropdown(self.data.voices, label='Voice')

            with gr.Row():
                self.progress_control = gr.Slider()
                self.total_duration = gr.Label()

            self.text_control = gr.Label()
            self.audio_control = gr.Audio(autoplay=True, interactive=False)

            buttons = []
            with gr.Row():
                for button_caption in self.button_captions:
                    buttons.append(gr.Button(button_caption))

            self.file_id_control = gr.Label()
            controls = [self.progress_control, self.text_control, self.audio_control, self.file_id_control, self.total_duration]

            select_voice.change(self.cm_voice_change, inputs=[select_voice]).then(self.cm_next_sample, outputs=controls)
            for button in buttons:
                button.click(self.cm_feedback, inputs=[button]).then(self.cm_next_sample, outputs=controls)

            demo.load(self.cm_load).then(self.cm_next_sample, outputs=controls)

        return demo

