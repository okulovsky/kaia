"""
The NLU testbed on the neutral intents of TestbedIntents.

    python chara/nlu/testbed/run.py install     # builds and starts the deciders in Docker
    python chara/nlu/testbed/run.py generate    # paraphrases and negatives with the Ollama running on the host
    python chara/nlu/testbed/run.py run         # trains and opens the testbed
"""
import argparse
from pathlib import Path
import requests
from brainbox import BrainBox
from brainbox.deciders import Ollama, WhisperKenLM, Nemotron, Chroma, LlamaLoraServer, LlamaLoraSFTTrainer
from brainbox.framework import ISelfManagingDecider, BrainBoxSetup
from foundation_kaia.fork import Fork
from foundation_kaia.marshalling import FileLike
from foundation_kaia.misc import Loc
from avatar.daemon.streaming_stt_service import IntentSource
from chara.common import Chara
from chara.nlu.ner_training import NerTrainingPipeline
from chara.nlu.scripts import create_dataset, create_negatives
from chara.nlu.testbed import TestbedIntents, Stt, run_nlu_testbed
from kaia.app import KaiaAppSettings

FOLDER = Chara.Apis.content_folder/'nlu'/'testbed'
WORKING_FOLDER = Loc.data_folder/'nlu-testbed'


class NativeOllama(ISelfManagingDecider):
    """Ollama decider that sends the prompts to the Ollama running on the host, e.g. with Metal on a Mac"""
    def __init__(self, model: str):
        self.model = model

    def get_name(self):
        return 'Ollama'

    def question(self, prompt: str, system_prompt: str | None = None, options: Ollama.Options | None = None, image: FileLike | None = None) -> str:
        body = dict(model=self.model, prompt=prompt, stream=False)
        if system_prompt is not None:
            body['system'] = system_prompt
        if options is not None:
            body.update(options.to_body_fields())
        reply = requests.post('http://127.0.0.1:11434/api/generate', json=body, timeout=600)
        reply.raise_for_status()
        return reply.json()['response']


def install():
    settings = KaiaAppSettings()
    settings.kaia = None
    settings.avatar_server = None
    settings.avatar_processor = None
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    app = settings.create_app(WORKING_FOLDER)
    setup = (BrainBoxSetup()
             .up(Nemotron, model='multilingual').up(WhisperKenLM).up(Chroma)
             .up(LlamaLoraServer, parameter=NerTrainingPipeline().model_id).up(LlamaLoraSFTTrainer))
    with Fork(app.brainbox_server):
        app.brainbox_api.wait_for_connection(30)
        setup.execute(app.brainbox_api)


def generate(model: str, folder: Path):
    with BrainBox.Api.serverless_test([NativeOllama(model)]) as api:
        Chara.Apis.brainbox_api = api
        create_dataset(TestbedIntents.get_templates(), model, folder=folder)
        create_negatives(model, folder=folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('install', 'generate', 'run'))
    parser.add_argument('--model', default='mistral', help='The model of the host Ollama that generates the dataset')
    parser.add_argument('--stt', default=Stt.NEMOTRON, choices=Stt.ALL)
    parser.add_argument('--intent-source', default=IntentSource.CHROMA, choices=IntentSource.ALL)
    parser.add_argument('--folder', default=str(FOLDER), help='The folder of dataset.json and negatives.txt')
    args = parser.parse_args()
    if args.action == 'install':
        install()
    elif args.action == 'generate':
        generate(args.model, Path(args.folder))
    else:
        run_nlu_testbed(TestbedIntents.get_templates(), Path(args.folder), args.stt, args.intent_source, working_folder=WORKING_FOLDER)
