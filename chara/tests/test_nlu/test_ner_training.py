from unittest import TestCase
from brainbox.deciders.text.llama_lora_sft_trainer.app.interface import TrainingRun
from chara.nlu.ner_training import NerTrainingPipeline


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


class NerTrainingPipelineTestCase(TestCase):
    def test_samples(self):
        pipeline = NerTrainingPipeline(samples_per_intent=10, validation_per_intent=100, test_share=0.25)
        train, validation = pipeline._samples(TEXT_DATASET)

        self.assertEqual(set(), {s['INPUT'] for s in train} & {s['INPUT'] for s in validation})
        self.assertNotIn('time', {s['intent'] for s in train + validation})
        self.assertEqual(10, sum(s['intent'] == 'timer' for s in train))
        samples = {s['INPUT']: s['OUTPUT'] for s in train + validation}
        self.assertEqual('\nduration: 0:05:00', samples['set the timer for 0 minutes en'])
        self.assertEqual('\n-', samples['cancel the timer'])
        self.assertEqual('\nindex: 2', samples['cancel the second timer'])

    def test_report(self):
        validation = [
            dict(INPUT='a', OUTPUT='\nindex: 2', intent='x.cancel', language='en'),
            dict(INPUT='b', OUTPUT='\n-', intent='x.cancel', language='ru'),
        ]
        run = TrainingRun('model', NerTrainingPipeline.ADAPTER, 'guid', None)
        report = NerTrainingPipeline()._report(run, validation, ['\nindex: 2', 'index: 3'])
        self.assertEqual(0.5, report.accuracy['all'])
        self.assertEqual(1, report.accuracy['en'])
        self.assertEqual(0, report.accuracy['ru'])
        self.assertEqual(1, len(report.errors))
