from unittest import TestCase
from ....framework import TestReport, File, BrainBoxApi, BrainBoxTask
from .api import RhasspyKaldi
from pathlib import Path

def english(api: BrainBoxApi, tc: TestCase):
    yield TestReport.section("English model")
    model_name = 'test_english'

    sentences = '''
[timer]
minutes = one | two | three | four | five | six | seven | eight | nine | ten
Set the timer for <minutes> {minutes} minutes
        
[time]
What time is it
    '''.strip()
    api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name, 'en', sentences))
    yield TestReport.last_call(api).with_comment("Training the model")


    file = File.read(Path(__file__).parent / 'files/timer.wav')
    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file, model_name))
    yield TestReport.last_call(api).with_comment("Inference")
    tc.assertEqual('five', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('timer', result['fsticuffs'][0]['intent']['name'])





def german(api: BrainBoxApi, tc: TestCase):
    yield TestReport.section("German model")
    model_name = 'test_german'

    sentences = '''
[timer_de]
_minutes = zwei|drei|vier|fünf
Stelle den Timer auf <_minutes>{_minutes} Minuten    
    '''.strip()

    api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name,'de',sentences))
    yield TestReport.last_call(api).with_comment("Training the model")

    file = File.read(Path(__file__).parent / 'files/timer-de.wav')
    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file, model_name))
    yield TestReport.last_call(api).with_comment("Inference with a trained model")
    tc.assertEqual('fünf', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('timer_de', result['fsticuffs'][0]['intent']['name'])



def english_custom(api: BrainBoxApi, tc: TestCase):
    yield TestReport.section("English model with custom pronunciation")
    model_name = 'test_english_custom_words'

    sentences = '''
[order]
_order = Shi|Ukha|Borsh
I order <_order>{_order}    
        '''.strip()

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name, 'en', sentences))
    yield TestReport.last_call(api).with_comment("Training with words that are missing from the dictionary. The training returns the list of words in question.")
    tc.assertDictEqual(
        dict(borsh="b 'O r S", ukha="j u k V"),
        result['unknown_words']
    )

    api.execute(BrainBoxTask.call(RhasspyKaldi).phonemes('en'))
    yield TestReport.last_call(api).with_comment("Transcription can be provided for these words. The symbols for this transcription are rather peculiar, and are returned by this endpoint.")

    custom_words = {
        'shi' : "S i",
        'ukha': "u h 'A",
        'borsh': 'b o r S'
    }
    result = api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name, 'en', sentences, custom_words))
    yield TestReport.last_call(api).with_comment("The training with the transcription of custom words specified")
    tc.assertEqual(0, len(result['unknown_words']))

    file = File.read(Path(__file__).parent / 'files/ukha.wav')
    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file, model_name))
    yield TestReport.last_call(api).with_comment("The inference with custom pronunciation")
    tc.assertEqual('ukha', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('order', result['fsticuffs'][0]['intent']['name'])




