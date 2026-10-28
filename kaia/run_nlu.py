import argparse
from dataclasses import dataclass
import time
import webbrowser
from pathlib import Path
from kaia.app import KaiaAppSettings, AvatarDaemonAppSettings, KaiaApp, AssistantFactory
from foundation_kaia.misc import Loc
from foundation_kaia.fork import Fork
from avatar.app import compile_frontend
from avatar.daemon import StreamingSTTService, NLUService, State
from avatar.daemon.streaming_stt_service import IntentSource
from brainbox import BrainBox
from brainbox.deciders import WhisperKenLM, Nemotron, Chroma, LlamaLoraSFTTrainer, LlamaLoraServer, Ollama
from grammatron import Template
from chara.common import Chara
from chara.nlu.ner_training import NerTrainingPipeline
from chara.nlu.scripts import create_dataset, create_negatives, train_ultimate_nlu
from chara.nlu.scripts.common import default_ultimate_nlu_folder


parser = argparse.ArgumentParser()
parser.add_argument('--folder', default=str(default_ultimate_nlu_folder()),
                    help='Folder with dataset.json and, optionally, negatives.txt, see chara/nlu/scripts')
parser.add_argument('--generate', action='store_true',
                    help='Adds a new run of paraphrases and negatives to the folder before the training; needs the LLM in BrainBox (Ollama)')
parser.add_argument('--model', default='mistral-small', help='The LLM that generates the dataset and the negatives')
parser.add_argument('--intent-source', default=IntentSource.CHROMA, choices=IntentSource.ALL,
                    help='Who decides the intent: Chroma, the LoRA of the slots, or their agreement')


def kaia_intent_templates() -> list[Template]:
    """The intents of the Kaia assistant: the templates the dataset paraphrases"""
    assistant = AssistantFactory(None).create_assistant(None)
    templates = []
    for pack in assistant.get_intents():
        templates.extend(pack.templates)
    return templates


@dataclass
class NluAvatarDaemonAppSettings(AvatarDaemonAppSettings):
    slots_adapter: str|None = None
    slots_model: str = 'gemma-3-270m-it'
    intent_source: str = IntentSource.CHROMA

    def create_stt_service(self, app: KaiaApp, state: State):
        return StreamingSTTService(state, app.brainbox_cache_folder)

    def create_nlu_service(self, app: KaiaApp, state: State):
        return NLUService(slots_adapter=self.slots_adapter, slots_model=self.slots_model, intent_source=self.intent_source)


if __name__ == '__main__':
    args = parser.parse_args()
    folder = Path(args.folder)

    working_folder = Loc.data_folder / 'demo'
    compile_frontend(working_folder / 'avatar' / 'frontend')

    settings = KaiaAppSettings()
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    settings.custom_avatar_resources_folder = Loc.root_folder/'kaia/app/files/avatar-resources'
    ner = NerTrainingPipeline()
    # Nemotron recognizes the speech, WhisperKenLM is needed only for the training of KenLM
    settings.brainbox_setup.up(Nemotron, model='multilingual').up(WhisperKenLM).up(Chroma).up(LlamaLoraServer, parameter=ner.model_id).up(LlamaLoraSFTTrainer)
    if args.generate:
        # The model given by --model must be available in this Ollama
        settings.brainbox_setup.up(Ollama)
    settings.avatar_processor = NluAvatarDaemonAppSettings(
        slots_adapter=ner.ADAPTER, slots_model=ner.model_id, intent_source=args.intent_source,
    )
    app = settings.create_app(working_folder)

    with Fork(app.brainbox_server):
        app.brainbox_api.wait_for_connection(30)
        settings.brainbox_setup.execute(app.brainbox_api)

        # A separate client: the app's one is pickled into the forks, and API clients keep the last request,
        # which for uploads holds a generator that cannot be pickled.
        Chara.Apis.brainbox_api = BrainBox.Api(app.brainbox_api.base_url)
        if args.generate:
            create_dataset(kaia_intent_templates(), args.model, folder=folder)
            create_negatives(args.model, folder=folder)
        # Restored from the cache while the dataset and the negatives are the same
        print(train_ultimate_nlu(folder))

        app.get_fork_app(None).run()
        app.avatar_api.wait_for_connection(30)

        webbrowser.open('http://127.0.0.1:13002')
        while True:
            time.sleep(1)
