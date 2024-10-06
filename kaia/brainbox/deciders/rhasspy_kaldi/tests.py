from unittest import TestCase
from ...core import BrainBoxApi
from .api import RhasspyKaldi
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult, File, BrainBoxTaskPack
from kaia.dub import Template, IntentsPack
from kaia.dub.languages.en import CardinalDub, StringSetDub
from pathlib import Path
import json



def english(api: BrainBoxApi, tc: TestCase):
    yield IntegrationTestResult(0, "English model")
    intents = IntentsPack(
        'test_1',
        (
            Template('Set the timer for {minutes} minutes', minutes=CardinalDub(1, 10)).with_name('timer'),
            Template('What time is it?').with_name('time')
        ))

    api.execute(BrainBoxTask.call(RhasspyKaldi).train(intents_pack=intents))

    file = File.read(Path(__file__).parent / 'files/timer.wav')
    yield IntegrationTestResult(1, None, file)

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file=file).to_task(decider_parameters='test_1'))
    tc.assertEqual('five', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('timer', result['fsticuffs'][0]['intent']['name'])

    js = File("response.json", json.dumps(result), File.Kind.Json)
    yield IntegrationTestResult(1, None, js)


def german(api: BrainBoxApi, tc: TestCase):
    yield IntegrationTestResult(0, "German model")
    intents = IntentsPack(
        'test_2',
        (
            Template(
                "Stelle den Timer auf {minutes} Minuten",
                minutes=StringSetDub(['zwei', 'drei', 'vier', 'fünf'])).with_name('timer_de'),
        ),
        language='de',
    )

    api.execute(BrainBoxTask.call(RhasspyKaldi).train(intents_pack=intents))

    file = File.read(Path(__file__).parent / 'files/timer-de.wav')
    yield IntegrationTestResult(1, None, file)

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file=file).to_task(decider_parameters='test_2'))
    tc.assertEqual('fünf', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('timer_de', result['fsticuffs'][0]['intent']['name'])

    js = File("response.json", json.dumps(result), File.Kind.Json)
    yield IntegrationTestResult(1, None, js)


def english_custom(api: BrainBoxApi, tc: TestCase):
    yield IntegrationTestResult(0, "English model with custom words")
    intents = IntentsPack(
        'test_3',
        (Template("I order {order}", order=StringSetDub(["Shi", "Ukha", "Borsh"])).with_name('order'),),
    )
    result = api.execute(BrainBoxTask.call(RhasspyKaldi).train(intents_pack=intents))
    print(result)
    tc.assertDictEqual(
        dict(borsh="b 'O r S", ukha="j u k V"),
        result['unknown_words']
    )
    print(api.execute(BrainBoxTask.call(RhasspyKaldi).phonemes(language='en')))
    intents.custom_words = {
        'shi' : "S i",
        'ukha': "u h 'A",
        'borsh': 'b o r S'
    }
    intents.name='test_4'
    result = api.execute(BrainBoxTask.call(RhasspyKaldi).train(intents_pack=intents))

    tc.assertEqual(0, len(result['unknown_words']))

    file = File.read(Path(__file__).parent / 'files/ukha.wav')
    yield IntegrationTestResult(0, None, file)

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file=file).to_task(decider_parameters='test_4'))
    tc.assertEqual('ukha', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('order', result['fsticuffs'][0]['intent']['name'])

    js = File("response.json", json.dumps(result), File.Kind.Json)
    yield IntegrationTestResult(1, None, js)



