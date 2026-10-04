import json
import random
from collections import defaultdict
from dataclasses import dataclass, field
from brainbox.deciders.text.llama_lora_sft_trainer.app.interface import TrainingSettings
from chara.common import Chara
from ..slm_training.pipeline import LlamaLoraPipeline, upload_checkpoint
from ..slm_training.stats import TrainingRunStats, CheckpointValStats
from .dataset import record_to_sample


def default_training_settings() -> TrainingSettings:
    settings = TrainingSettings()
    # One checkpoint per epoch, each is validated and the best one is deployed.
    # fp16 is off, so the training also runs on CPU (e.g. BrainBox on a Mac)
    settings.training_args.update(save_strategy='epoch', save_total_limit=None, fp16=False)
    return settings


@dataclass
class NerTrainingReport:
    stats: TrainingRunStats
    deployed_checkpoint: int
    accuracy: dict[str, float] = field(default_factory=dict)

    def __str__(self):
        lines = [f'Slots exact match on held-out texts, checkpoint {self.deployed_checkpoint} deployed:']
        for key, value in self.accuracy.items():
            lines.append(f'  {key:20} {value:.1%}')
        return '\n'.join(lines)


class NerTrainingPipeline:
    """
    Trains the slots model of NluRecognitionSetup: a LoRA adapter for LlamaLoraServer that receives
    the recognized text and outputs the values of the template's variables
    (the format is in avatar/daemon/stt_service/stt/nlu_slots.py).

    Only the intents with variables are used. Every checkpoint is validated on the records with held-out texts,
    and the best one is deployed to LlamaLoraServer as the adapter ADAPTER.
    """
    ADAPTER = 'nlu-slots'

    def __init__(self,
                 model_id: str = 'gemma-3-270m-it',
                 samples_per_intent: int | None = 400,
                 validation_per_intent: int = 50,
                 test_share: float = 0.15,
                 settings: TrainingSettings | None = None,
                 seed: int = 0,
                 ):
        self.model_id = model_id
        self.samples_per_intent = samples_per_intent
        self.validation_per_intent = validation_per_intent
        self.test_share = test_share
        self.settings = settings if settings is not None else default_training_settings()
        self.seed = seed

    def __call__(self, text_dataset: list[dict]) -> NerTrainingReport:
        @Chara.phase
        def samples():
            train, validation = self._samples(text_dataset)
            for name, data in (('train', train), ('validation', validation)):
                (Chara.current.folder / f'{name}.jsonl').write_text(
                    ''.join(json.dumps(dict(INPUT=s['INPUT'], OUTPUT=s['OUTPUT']), ensure_ascii=False) + '\n' for s in data)
                )
            return Chara.current.folder, validation

        folder, validation = samples
        pipeline = LlamaLoraPipeline(self.model_id, self.settings, max_tokens=24)
        stats = Chara.call(pipeline)(self.ADAPTER, folder / 'train.jsonl', folder / 'validation.jsonl')
        best = stats.get_best_checkpoint()

        @Chara.phase
        def deployment():
            upload_checkpoint(stats.training_run, best.number, self.ADAPTER)

        return NerTrainingReport(stats, best.number, self._accuracy(best, validation))

    def _samples(self, text_dataset: list[dict]):
        intents_with_values = {r['intent'] for r in text_dataset if r['values']}
        records = [r for r in text_dataset if r['intent'] in intents_with_values]
        rnd = random.Random(self.seed)
        texts = sorted({r['text'] for r in records})
        test_texts = set(rnd.sample(texts, int(len(texts) * self.test_share)))
        by_intent = defaultdict(lambda: ([], []))
        for record in records:
            sample = record_to_sample(record)
            if sample is None:
                continue
            sample.update(intent=record['intent'], language=record['language'])
            by_intent[record['intent']][record['text'] in test_texts].append(sample)
        train, validation = [], []
        for intent in sorted(by_intent):
            intent_train, intent_validation = by_intent[intent]
            rnd.shuffle(intent_train)
            rnd.shuffle(intent_validation)
            train.extend(intent_train[:self.samples_per_intent])
            validation.extend(intent_validation[:self.validation_per_intent])
        rnd.shuffle(train)
        return train, validation

    def _accuracy(self, checkpoint: CheckpointValStats, validation: list[dict]) -> dict[str, float]:
        counts = defaultdict(lambda: [0, 0])
        for sample, result in zip(validation, checkpoint.generation_results):
            for key in ('all', sample['language'], sample['intent'].split('.')[-1]):
                counts[key][0] += result.is_correct()
                counts[key][1] += 1
        return {key: correct / total for key, (correct, total) in counts.items()}
