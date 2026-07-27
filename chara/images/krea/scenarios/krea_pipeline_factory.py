from ...common import PipelineFactory
from pathlib import Path

class KreaPipelineFactory(PipelineFactory):
    def __init__(self, llm_model: str, scripts_folder: tuple[Path,...]):
        super().__init__(llm_model, scripts_folder + (Path(__file__).parent,))
