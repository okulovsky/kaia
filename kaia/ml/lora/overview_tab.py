import subprocess
import sys

import gradio as gr
from kaia.infra.gradio import *
from kaia.ml.lora import OverviewController
from pathlib import Path
from kaia.infra import FileIO

def empty_handler():
    pass

class OverviewTab:
    def __init__(self, controller: OverviewController):
        self.controller = controller

    def add_reload_data_event(self, endpoint):
        return (
            endpoint
            .then(self._reload_data, outputs=self.controls)
        )

    def _reload_data(self):
        html = self.controller.load_status()
        return {self.html: html}

    def _on_crop_message(self):
        return gr.update(label="The window with the cropped editor will open. Close it when you're done")

    def _on_crop(self):
        self.controller.run_croper()
        return gr.update(label="Current task", value="Ready")

    def _on_ai_message(self):
        return gr.update(label="Upscale/Interrogation tasks are running in Brainbox")

    def _on_ai(self):
        path = Path(__file__).parent/'test'
        FileIO.write_pickle(self.controller, path)
        subprocess.call([
            sys.executable,
            Path(__file__).parent/'run_ai.py',
            path
            ])
        return gr.update(label="Current task", value="Ready")

    def create_interface(self):
        self.controls = []
        with gr.Tab('Overview') as tab:
            self.html = gr.HTML()
            self.controls.append(self.html)
            tab.select(empty_handler).feed(self.add_reload_data_event)

            self.status = gr.Label("Ready", label="Current task")
            with gr.Row():
                self.reload = gr.Button("Reload")
                self.reload.click(empty_handler).feed(self.add_reload_data_event)

                self.run_ai = gr.Button("Run Interrogation/Upscale")
                (
                    self.run_ai.click(self._on_ai_message, outputs=[self.status])
                    .then(self._on_ai, outputs=[self.status])
                    .feed(self.add_reload_data_event)
                )

                self.run_crop = gr.Button("Run cropper")
                (
                    self.run_crop.click(self._on_crop_message, outputs=[self.status])
                    .then(self._on_crop, outputs=[self.status]).
                    feed(self.add_reload_data_event)
                )


