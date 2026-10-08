from unittest import TestCase
from unittest.mock import patch
from brainbox import BrainBox
from brainbox.deciders import Collector
from foundation_kaia.misc import Loc
from chara.common import Chara
from chara.nlu.ner_training import NerTrainingPipeline
from chara.tests.test_nlu.test_slm_training.test_pipeline import (
    LlamaLoraSFTTrainerMock, LlamaLoraServerMock, _upload_run_files, CHECKPOINTS,
)


def _timer(i: int, language: str = 'en') -> dict:
    return dict(
        text=f'set the timer for {i} minutes {language}', intent='timer', language=language,
        values=[dict(name='duration', type='TimedeltaDub', value='five minutes')],
    )


TEXT_DATASET = (
    [_timer(i) for i in range(20)]
    + [_timer(i, 'ru') for i in range(20)]
    + [dict(text='cancel the timer', intent='cancel', language='en', values=[])]
    + [dict(text=f'cancel the {w} timer', intent='cancel', language='en',
            values=[dict(name='index', type='OrdinalDub', value=w)]) for w in ('first', 'second', 'third')]
    + [dict(text='what time is it', intent='time', language='en', values=[])]
)


class SlotsServerMock(LlamaLoraServerMock):
    """The middle checkpoint knows the answers, the others answer nothing"""
    def completion(self, *, task_name: str, prompt=None, prompts=None, max_tokens: int = 500):
        self.task_names.append(task_name)
        if task_name.endswith(f'_{CHECKPOINTS[1]}'):
            return ['\nduration: 5m\n' if 'set the timer' in p else '\n-\n' for p in prompts]
        return ['\n-\n' for _ in prompts]


class NerTrainingPipelineTestCase(TestCase):
    def test_samples(self):
        pipeline = NerTrainingPipeline(samples_per_intent=10, validation_per_intent=100, test_share=0.25, synthetic_timers_per_language=0)
        train, validation = pipeline._samples(TEXT_DATASET)

        self.assertEqual(set(), {s['INPUT'] for s in train} & {s['INPUT'] for s in validation})
        self.assertNotIn('time', {s['intent'] for s in train + validation})
        self.assertEqual(10, sum(s['intent'] == 'timer' for s in train))
        samples = {s['INPUT']: s['OUTPUT'] for s in train + validation}
        self.assertEqual('\nduration: 5m', samples['set the timer for 0 minutes en'])
        self.assertEqual('\n-', samples['cancel the timer'])
        self.assertEqual('\nindex: 2', samples['cancel the second timer'])

    def test_best_checkpoint_is_deployed(self):
        model_id = 'mock_model'
        trainer, server = LlamaLoraSFTTrainerMock(), SlotsServerMock()
        with Loc.create_test_folder() as folder, patch('chara.nlu.slm_training.pipeline.restart_llama_lora_server'):
            with BrainBox.Api.serverless_test([server, trainer, Collector()]) as api:
                Chara.Apis.brainbox_api = api
                _upload_run_files(api, model_id, NerTrainingPipeline.ADAPTER)
                Chara.start(folder)
                report = Chara.call(NerTrainingPipeline(model_id=model_id, test_share=0.25, synthetic_timers_per_language=0))(TEXT_DATASET)
                adapters = api.resources('LlamaLoraServer').list(f'models/{model_id}/lora_adapters')

        self.assertEqual(CHECKPOINTS[1], report.deployed_checkpoint)
        self.assertEqual([f'{NerTrainingPipeline.ADAPTER}.gguf'], adapters)
        self.assertGreater(report.accuracy['all'], 0.5)
        self.assertEqual(1, report.accuracy['timer'])
