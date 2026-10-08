import argparse
import json
from pathlib import Path
from chara.common import Chara
from chara.nlu.ner_training import NerTrainingPipeline

# Trains and deploys the slots adapter of NluRecognitionSetup to the BrainBox at CHARA_BRAINBOX_URL.
# LlamaLoraSFTTrainer and LlamaLoraServer must be installed there.
# The results are cached: to retrain, delete the cache folder.

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--datasets', default=str(Chara.Apis.content_folder / 'nlu/datasets'))
    parser.add_argument('--samples-per-intent', type=int, default=400)
    args = parser.parse_args()

    text_dataset = json.loads((Path(args.datasets) / 'text-dataset.json').read_text())
    Chara.start(Chara.Apis.cache_folder / 'nlu/ner-training')
    report = Chara.call(NerTrainingPipeline(samples_per_intent=args.samples_per_intent))(text_dataset)
    print(report)
