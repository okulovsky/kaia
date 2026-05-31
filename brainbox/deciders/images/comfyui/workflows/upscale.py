from .workflow import IWorkflow
from foundation_kaia.marshalling import FileLike
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class Upscale(IWorkflow):
    input_filename: FileLike
    model_name: str = '4x-AnimeSharp.pth'
    width: int = 1024
    height: int = 1024

    def create_workflow(self):
        js = json.loads((Path(__file__).parent/'upscale.json').read_text())
        IWorkflow.make_substitution(js, 'image', 'input_0', 'Load Image')
        IWorkflow.make_substitution(js, 'model_name', self.model_name)
        IWorkflow.make_substitution(js, 'width', self.width, "Upscale Image")
        IWorkflow.make_substitution(js, 'height', self.height, "Upscale Image")
        return js

    def create_file_arguments(self):
        return [self.input_filename]





