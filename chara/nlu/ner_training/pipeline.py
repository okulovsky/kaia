import json
import random
from collections import defaultdict
from dataclasses import dataclass, field
from brainbox.deciders import LlamaLoraSFTTrainer, LlamaLoraServer
from brainbox.deciders.text.llama_lora_sft_trainer.app.interface import TrainingSettings, TrainingRun
from foundation_kaia.marshalling import TypeTools
from chara.common import Chara
from .dataset import record_to_sample


def default_training_settings() -> TrainingSettings:
    settings = TrainingSettings()
    # One checkpoint per epoch, and only the last one is kept: it is the one deployed.
    # fp16 is off, so the training also runs on CPU (e.g. BrainBox on a Mac)
    settings.training_args.update(save_strategy='epoch', save_total_limit=1, fp16=False)
    return settings


@dataclass
class NerTrainingReport:
    training_run: TrainingRun
    accuracy: dict[str, float] = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)

    def __str__(self):
        lines = [f'Slots exact match on held-out texts, adapter {self.training_run.adapter_name}:']
        for key, value in self.accuracy.items():
            lines.append(f'  {key:20} {value:.1%}')
        return '\n'.join(lines)


class NerTrainingPipeline:
    """
    Trains the slots model of NluRecognitionSetup: a LoRA adapter for LlamaLoraServer that receives
    the recognized text and outputs the values of the template's variables (see avatar ... nlu_slots.py).

    Only the intents that have variables are used. The adapter is trained on `samples_per_intent` records,
    deployed to LlamaLoraServer and then evaluated on the records with held-out texts.
    """
    ADAPTER = 'nlu-slots'

    def __init__(self,
                 model_id: str = 'gemma-3-270m-it',
                 samples_per_intent: int | None = 400,
                 validation_per_intent: int = 50,
                 test_share: float = 0.15,
                 settings: TrainingSettings | None = None,
                 validation_batch_size: int = 32,
                 seed: int = 0,
                 ):
        self.model_id = model_id
        self.samples_per_intent = samples_per_intent
        self.validation_per_intent = validation_per_intent
        self.test_share = test_share
        self.settings = settings if settings is not None else default_training_settings()
        self.validation_batch_size = validation_batch_size
        self.seed = seed

    def __call__(self, text_dataset: list[dict]) -> NerTrainingReport:
        @Chara.phase
        def samples():
            return self._samples(text_dataset)

        train, validation = samples

        @Chara.phase
        def training():
            dataset = Chara.current.folder / 'train.jsonl'
            dataset.write_text(''.join(json.dumps(s, ensure_ascii=False) + '\n' for s in train))
            return self._train(dataset)

        @Chara.phase
        def deployment():
            self._deploy(training)

        @Chara.phase
        def outputs():
            return self._complete([s['INPUT'] for s in validation])

        return self._report(training, validation, outputs)

    def _samples(self, text_dataset: list[dict]):
        records = [r for r in text_dataset if r['intent'] in {r['intent'] for r in text_dataset if r['values']}]
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

    def _train(self, dataset) -> TrainingRun:
        api = Chara.Apis.brainbox_api
        task = LlamaLoraSFTTrainer.new_task().train(self.model_id, self.ADAPTER, self.settings, dataset)
        log_file = api.join(api.add(task))
        # The training streams report lines; the last one carries the TrainingRun
        for line in api.cache.read(log_file).decode('utf-8').split('\n'):
            if line.strip():
                item = json.loads(line)
                if item['result'] is not None:
                    return TypeTools.deserialize(item['result'], TrainingRun)
        raise ValueError(f"The training of {self.ADAPTER} did not return the training run")

    def _deploy(self, run: TrainingRun):
        api = Chara.Apis.brainbox_api
        folder = f'experiments/{run.model_id}/{run.adapter_name}/{run.guid}/gguf_checkpoints'
        checkpoints = api.resources(LlamaLoraSFTTrainer).list(folder, suffix='.gguf')
        if len(checkpoints) == 0:
            raise ValueError(f"No GGUF checkpoints in {folder}")
        last = max(checkpoints, key=lambda name: int(name.split('/')[-1].split('.')[0].split('-')[1]))
        api.resources(LlamaLoraServer).upload(
            f'models/{self.model_id}/lora_adapters/{self.ADAPTER}.gguf',
            api.resources(LlamaLoraSFTTrainer).open(f'{folder}/{last.split("/")[-1]}'),
        )
        # LlamaLoraServer loads the adapters at the start, so the running instances must be restarted
        for controller in api.controllers.status().controllers:
            if controller.name == 'LlamaLoraServer':
                for instance in controller.instances:
                    api.controllers.stop(controller.name, instance.instance_id)

    def _complete(self, prompts: list[str]) -> list[str]:
        outputs = []
        for start in range(0, len(prompts), self.validation_batch_size):
            batch = prompts[start:start + self.validation_batch_size]
            result = Chara.Apis.brainbox_api.execute(
                LlamaLoraServer.new_task(parameter=self.model_id).completion(
                    task_name=self.ADAPTER, prompts=batch, max_tokens=24,
                )
            )
            outputs.extend(result)
        return outputs

    def _report(self, run: TrainingRun, validation: list[dict], outputs: list[str]) -> NerTrainingReport:
        report = NerTrainingReport(run)
        counts = defaultdict(lambda: [0, 0])
        for sample, output in zip(validation, outputs):
            hit = output.strip() == sample['OUTPUT'].strip()
            for key in ('all', sample['language'], sample['intent'].split('.')[-1]):
                counts[key][0] += hit
                counts[key][1] += 1
            if not hit:
                report.errors.append(dict(input=sample['INPUT'], expected=sample['OUTPUT'].strip(), output=output.strip()))
        report.accuracy = {key: hit / n for key, (hit, n) in counts.items()}
        return report
