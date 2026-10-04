import argparse
import time
import webbrowser
from pathlib import Path
from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc
from foundation_kaia.fork import Fork
from avatar.app import compile_frontend
from avatar.daemon import NluRecognitionSetup
from brainbox.deciders import WhisperKenLM, Chroma
from chara.common import Chara
from chara.nlu.nlu_training import NluTrainingPipeline, load_nlu_datasets


parser = argparse.ArgumentParser()
parser.add_argument('--datasets', default=str(Chara.Apis.content_folder / 'nlu/datasets'),
                    help='Folder with text-dataset.json and, optionally, to_zip/samples.json')


if __name__ == '__main__':
    args = parser.parse_args()
    text_dataset, voice_samples = load_nlu_datasets(Path(args.datasets))

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

        # Trained once and then restored from the cache, see chara/nlu/run_nlu_training.py
        Chara.Apis.brainbox_api = app.brainbox_api
        Chara.start(Chara.Apis.cache_folder / 'nlu/nlu-training')
        print(Chara.call(NluTrainingPipeline())(text_dataset, voice_samples))

        app.get_fork_app(None).run()
        app.avatar_api.wait_for_connection(30)

        webbrowser.open('http://127.0.0.1:13002')
        while True:
            time.sleep(1)
