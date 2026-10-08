import argparse
from pathlib import Path
from chara.common import Chara
from chara.nlu.nlu_training import NluTrainingPipeline, load_nlu_datasets

# Trains and deploys the models of NluRecognitionSetup to the BrainBox at CHARA_BRAINBOX_URL.
# WhisperKenLM and Chroma must be installed there.
# The results are cached: to retrain after the datasets have changed, delete the cache folder.

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--datasets', default=str(Chara.Apis.content_folder / 'nlu/datasets'))
    parser.add_argument('--voices-per-language', type=int, default=100)
    args = parser.parse_args()

    text_dataset, voice_samples = load_nlu_datasets(Path(args.datasets))
    Chara.start(Chara.Apis.cache_folder / 'nlu/nlu-training')
    report = Chara.call(NluTrainingPipeline(voices_per_language=args.voices_per_language))(text_dataset, voice_samples)
    print(report)
