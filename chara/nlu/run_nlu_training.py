import argparse
from pathlib import Path
from chara.common import Chara
from chara.nlu.datasets.text_dataset import TextDatasetPipeline, kaia_intent_templates, MOODS, LANGUAGES
from chara.nlu.nlu_training import NluTrainingPipeline, load_nlu_datasets
from chara.nlu.ner_training import NerTrainingPipeline
from chara.nlu.nlu_pipeline import NluDatasetStore, NluPipeline

# The whole NLU of NluRecognitionSetup on the BrainBox at CHARA_BRAINBOX_URL:
# generates a new round of the text dataset with the LLM (Ollama) and adds it to the stored dataset,
# then trains and deploys KenLM (WhisperKenLM), the intent index (Chroma) and the slots adapter
# (LlamaLoraSFTTrainer, LlamaLoraServer). These deciders must be installed there.
#
# Every run adds to the dataset, nothing is overwritten. A run that failed continues from where it stopped.

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--datasets', default=str(Chara.Apis.content_folder / 'nlu/datasets'),
                        help='Folder of the text dataset rounds; voiced samples, if any, are in to_zip/')
    parser.add_argument('--rounds', type=int, default=1, help='How many rounds of the text dataset to generate')
    parser.add_argument('--no-generation', action='store_true', help='Only train on the stored dataset')
    parser.add_argument('--model', default='mistral-small', help='The LLM that paraphrases the templates')
    parser.add_argument('--no-slots', action='store_true', help='Do not train the slots adapter')
    parser.add_argument('--voices-per-language', type=int, default=100)
    args = parser.parse_args()

    datasets = Path(args.datasets)
    generator = TextDatasetPipeline(args.model, kaia_intent_templates(), list(LANGUAGES), list(MOODS))
    pipeline = NluPipeline(
        NluDatasetStore(datasets),
        Chara.Apis.cache_folder / 'nlu',
        generator,
        NluTrainingPipeline(voices_per_language=args.voices_per_language),
        None if args.no_slots else NerTrainingPipeline(),
    )

    if not args.no_generation:
        for _ in range(args.rounds):
            number = pipeline.generate_round()
            print(f'Round {number} of the text dataset is generated')

    _, voice_samples = load_nlu_datasets(datasets)
    print(pipeline.train(voice_samples))
