import hashlib
import json
from pathlib import Path
from chara.common import Chara
from chara.nlu.nlu_training import NluTrainingPipeline
from chara.nlu.ner_training import NerTrainingPipeline
from .common import default_ultimate_nlu_folder


def _train(dataset: list[dict]) -> str:
    nlu_report = Chara.call(NluTrainingPipeline())(dataset)
    ner_report = Chara.call(NerTrainingPipeline())(dataset)
    return f'{nlu_report}\n{ner_report}'


def train_ultimate_nlu(folder: Path | None = None) -> str:
    """
    Trains and deploys on the BrainBox everything NluRecognitionSetup needs from `folder`/dataset.json:
    KenLM, the Chroma intent index and the slots adapter. The cache is in `folder`/$training/<hash of the dataset>,
    so a failed run continues, and a new dataset is trained anew. Returns the reports.
    """
    if folder is None:
        folder = default_ultimate_nlu_folder()
    dataset_path = folder/'dataset.json'
    dataset = json.loads(dataset_path.read_text())
    fingerprint = hashlib.sha256(dataset_path.read_bytes()).hexdigest()[:16]

    Chara.start(folder/'$training'/fingerprint)
    return Chara.call(_train)(dataset)
