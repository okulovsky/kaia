from typing import Iterable
from ....framework import File, SelfTestCase
from pathlib import Path


def english() -> Iterable[SelfTestCase]:
    from .api import RhasspyKaldi
    model_name = 'test_english'
    sentences = '''
[timer]
minutes = one | two | three | four | five | six | seven | eight | nine | ten
Set the timer for <minutes> {minutes} minutes

[time]
What time is it
    '''.strip()
    file = File.read(Path(__file__).parent / 'files/timer.wav')

    yield SelfTestCase(RhasspyKaldi.new_task().train(model_name, 'en', sentences), None)

    def check(result, api, tc):
        tc.assertEqual('five', result['fsticuffs'][0]['entities'][0]['raw_value'])
        tc.assertEqual('timer', result['fsticuffs'][0]['intent']['name'])
    yield SelfTestCase(RhasspyKaldi.new_task().transcribe(file, model_name), check)


def german() -> Iterable[SelfTestCase]:
    from .api import RhasspyKaldi
    model_name = 'test_german'
    sentences = '''
[timer_de]
_minutes = zwei|drei|vier|fünf
Stelle den Timer auf <_minutes>{_minutes} Minuten
    '''.strip()
    file = File.read(Path(__file__).parent / 'files/timer-de.wav')

    yield SelfTestCase(RhasspyKaldi.new_task().train(model_name, 'de', sentences), None)

    def check(result, api, tc):
        tc.assertEqual('fünf', result['fsticuffs'][0]['entities'][0]['raw_value'])
        tc.assertEqual('timer_de', result['fsticuffs'][0]['intent']['name'])
    yield SelfTestCase(RhasspyKaldi.new_task().transcribe(file, model_name), check)


def english_custom() -> Iterable[SelfTestCase]:
    from .api import RhasspyKaldi
    model_name = 'test_english_custom_words'
    sentences = '''
[order]
_order = Shi|Ukha|Borsh
I order <_order>{_order}
    '''.strip()
    custom_words = {
        'shi': "S i",
        'ukha': "u h 'A",
        'borsh': 'b o r S'
    }
    file = File.read(Path(__file__).parent / 'files/ukha.wav')

    yield SelfTestCase(
        RhasspyKaldi.new_task().train(model_name, 'en', sentences),
        lambda result, api, tc: tc.assertDictEqual(dict(borsh="b 'O r S", ukha="j u k V"), result['unknown_words'])
    )
    yield SelfTestCase(RhasspyKaldi.new_task().phonemes('en'), None)
    yield SelfTestCase(
        RhasspyKaldi.new_task().train(model_name, 'en', sentences, custom_words),
        lambda result, api, tc: tc.assertEqual(0, len(result['unknown_words']))
    )

    def check(result, api, tc):
        tc.assertEqual('ukha', result['fsticuffs'][0]['entities'][0]['raw_value'])
        tc.assertEqual('order', result['fsticuffs'][0]['intent']['name'])
    yield SelfTestCase(RhasspyKaldi.new_task().transcribe(file, model_name), check)
