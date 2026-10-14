import json
from dataclasses import dataclass
from pathlib import Path
from chara.common import Chara
from chara.nlu.nlu_training import NluTrainingPipeline, NluTrainingReport
from chara.nlu.ner_training import NerTrainingPipeline, NerTrainingReport
from .common import default_ultimate_nlu_folder, training_folder


@dataclass
class UltimateNluReport:
    nlu: NluTrainingReport
    ner: NerTrainingReport

    def __str__(self):
        return f'{self.nlu}\n{self.ner}'


def _train(dataset: list[dict]) -> UltimateNluReport:
    nlu_report = Chara.call(NluTrainingPipeline())(dataset)
    ner_report = Chara.call(NerTrainingPipeline())(dataset)
    return UltimateNluReport(nlu_report, ner_report)


def train_ultimate_nlu(folder: Path | None = None) -> UltimateNluReport:
    """
    Trains and deploys on the BrainBox everything NluRecognitionSetup needs from `folder`/dataset.json:
    KenLM, the Chroma intent index and the slots adapter. The cache and the artifacts are in
    `folder`/$training/<hash of the dataset>, so a failed run continues, and a new dataset is trained anew.
    """
    if folder is None:
        folder = default_ultimate_nlu_folder()
    dataset = json.loads((folder/'dataset.json').read_text())
    Chara.start(training_folder(folder))
    return Chara.call(_train)(dataset)
