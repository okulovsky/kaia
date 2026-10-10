import argparse
import time
import webbrowser
from pathlib import Path
from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc
from foundation_kaia.fork import Fork
from avatar.app import compile_frontend
from avatar.daemon import NluRecognitionSetup
from avatar.daemon.stt_service.stt import IntentSource
from brainbox import BrainBox
from brainbox.deciders import WhisperKenLM, Chroma, LlamaLoraSFTTrainer, LlamaLoraServer, Ollama
from chara.common import Chara
from chara.nlu.nlu_training import NluTrainingPipeline, load_nlu_datasets
from chara.nlu.ner_training import NerTrainingPipeline
from chara.nlu.nlu_pipeline import NluDatasetStore, NluPipeline
from chara.nlu.datasets.text_dataset import TextDatasetPipeline, kaia_intent_templates, MOODS, LANGUAGES


parser = argparse.ArgumentParser()
parser.add_argument('--datasets', default=str(Chara.Apis.content_folder / 'nlu/datasets'),
                    help='Folder with text-dataset.json and, optionally, to_zip/samples.json')
parser.add_argument('--generate-rounds', type=int, default=0,
                    help='New rounds of the text dataset to generate before the training; needs the LLM in BrainBox (Ollama)')
parser.add_argument('--model', default='mistral-small', help='The LLM that generates the text dataset')
parser.add_argument('--intent-source', default=IntentSource.CHROMA, choices=IntentSource.ALL,
                    help='Who decides the intent: Chroma, the LoRA of the slots, or their agreement')


if __name__ == '__main__':
    args = parser.parse_args()
    datasets = Path(args.datasets)
    _, voice_samples = load_nlu_datasets(datasets)

    working_folder = Loc.data_folder / 'demo'
    compile_frontend(working_folder / 'avatar' / 'frontend')

    settings = KaiaAppSettings()
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    settings.custom_avatar_resources_folder = Loc.root_folder/'kaia/app/files/avatar-resources'
    ner = NerTrainingPipeline()
    settings.brainbox_setup.up(WhisperKenLM).up(Chroma).up(LlamaLoraServer, parameter=ner.model_id).up(LlamaLoraSFTTrainer)
    if args.generate_rounds > 0:
        # The model given by --model must be available in this Ollama
        settings.brainbox_setup.up(Ollama)
    settings.avatar_processor.stt_setup = NluRecognitionSetup(
        slots_adapter=ner.ADAPTER, slots_model=ner.model_id, intent_source=args.intent_source,
    )
    app = settings.create_app(working_folder)

    with Fork(app.brainbox_server):
        app.brainbox_api.wait_for_connection(30)
        settings.brainbox_setup.execute(app.brainbox_api)

        # Trains on the stored dataset, restored from the cache while the dataset is the same.
        # New rounds of the dataset are generated only with --generate-rounds: it takes long (see chara/nlu/run_nlu_training.py).
        # A separate client: the app's one is pickled into the forks, and API clients keep the last request,
        # which for uploads holds a generator that cannot be pickled.
        Chara.Apis.brainbox_api = BrainBox.Api(app.brainbox_api.base_url)
        generator = TextDatasetPipeline(args.model, kaia_intent_templates(), list(LANGUAGES), list(MOODS))
        pipeline = NluPipeline(NluDatasetStore(datasets), Chara.Apis.cache_folder / 'nlu', generator, NluTrainingPipeline(), ner)
        for _ in range(args.generate_rounds):
            print(f'Round {pipeline.generate_round()} of the text dataset is generated')
        print(pipeline.train(voice_samples))

        app.get_fork_app(None).run()
        app.avatar_api.wait_for_connection(30)

        webbrowser.open('http://127.0.0.1:13002')
        while True:
            time.sleep(1)
