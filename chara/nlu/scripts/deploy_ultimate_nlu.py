import json
from pathlib import Path
from brainbox import BrainBox
from brainbox.deciders import Chroma, LlamaLoraServer, WhisperKenLM
from chara.common import Chara
from chara.nlu.ner_training import NerTrainingPipeline
from .common import default_ultimate_nlu_folder, training_folder
from .train_ultimate_nlu import UltimateNluReport


def deploy_ultimate_nlu(api: BrainBox.Api, folder: Path | None = None):
    """
    Deploys the artifacts of train_ultimate_nlu on the current `folder`/dataset.json to the BrainBox `api`,
    e.g. the one of a running Kaia. The KenLM model is uploaded, a running WhisperKenLM keeps the old one until restarted.
    The Chroma collection is imported with the saved embeddings; LlamaLoraServer picks up the uploaded adapter on the next request.
    """
    if folder is None:
        folder = default_ultimate_nlu_folder()
    training = Chara.from_folder(training_folder(folder))
    if not training.has_result:
        raise ValueError(f"The training in {training_folder(folder)} is not finished, run train_ultimate_nlu first")
    report: UltimateNluReport = training.result
    artifacts = report.nlu.deployment_folder
    ner = NerTrainingPipeline()

    api.resources(WhisperKenLM).upload('lm/lm.binary', artifacts/'lm.binary')
    print('KenLM is deployed')
    api.execute(Chroma.new_task().import_collection(json.loads((artifacts/'chroma_collection.json').read_text())))
    print('Chroma index is deployed')
    api.resources(LlamaLoraServer).upload(f'models/{ner.model_id}/lora_adapters/{ner.ADAPTER}.gguf', report.ner.adapter_file)
    print('Slots adapter is deployed')
