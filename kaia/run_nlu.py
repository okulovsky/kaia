import json
import sys
import time
import webbrowser
from pathlib import Path
from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc
from foundation_kaia.fork import Fork
from avatar.app import compile_frontend
from avatar.daemon import NluRecognitionSetup
from brainbox.deciders import WhisperKenLM, Chroma


KENLM_CORPUS = Loc.root_folder/'research/lm/corpus.txt'
INTENTS_DATASET = Loc.root_folder/'research/text-dataset.json'


def train_nlu(api, kenlm_corpus: Path, intents_dataset: Path):
    for path in (kenlm_corpus, intents_dataset):
        if not path.is_file():
            raise FileNotFoundError(f"{path} is required to train the NLU recognition setup")
    api.execute(WhisperKenLM.new_task().train_lm(kenlm_corpus.read_text()))
    dataset = json.loads(intents_dataset.read_text())
    utterances = [dict(text=d['text'], intent=d['intent'], language=d['language']) for d in dataset]
    api.execute(Chroma.new_task().train(utterances))


if __name__ == '__main__':
    working_folder = Loc.data_folder / 'demo'
    compile_frontend(working_folder / 'avatar' / 'frontend')

    settings = KaiaAppSettings()
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    settings.custom_avatar_resources_folder = Loc.root_folder/'kaia/app/files/avatar-resources'
    settings.brainbox_setup.up(WhisperKenLM).up(Chroma)
    settings.avatar_processor.stt_setup = NluRecognitionSetup()
    app = settings.create_app(working_folder)

    with Fork(app.brainbox_server):
        app.brainbox_api.wait_for_connection(5)
        settings.brainbox_setup.execute(app.brainbox_api)
        if '--skip-training' not in sys.argv:
            train_nlu(app.brainbox_api, KENLM_CORPUS, INTENTS_DATASET)
        app.get_fork_app(None).run()
        app.avatar_api.wait_for_connection(30)

        webbrowser.open('http://127.0.0.1:13002')
        while True:
            time.sleep(1)
