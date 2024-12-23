from unittest import TestCase
from ....framework import TestReport, File, BrainBoxApi, BrainBoxTask
from .api import RhasspyKaldi
from kaia.dub import Template, IntentsPack
from kaia.dub.languages.en import CardinalDub, StringSetDub
from pathlib import Path
import json

def english(api: BrainBoxApi, tc: TestCase):
    model_name = 'test_english'

    yield TestReport.H1("English model")

    sentences = '''
[timer]
minutes = one | two | three | four | five | six | seven | eight | nine | ten
Set the timer for <minutes> {minutes} minutes
        
[time]
What time is it
    '''.strip()
    yield TestReport.text("Grammar for training:")
    yield TestReport.code(sentences)
    api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name, 'en', sentences))


    yield TestReport.text("Input audio to transcribe:")
    file = File.read(Path(__file__).parent / 'files/timer.wav')
    yield TestReport.file(file)

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file, model_name))
    tc.assertEqual('five', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('timer', result['fsticuffs'][0]['intent']['name'])

    yield TestReport.text("Result:")
    yield TestReport.json(result)




def german(api: BrainBoxApi, tc: TestCase):
    model_name = 'test_german'

    yield TestReport.H1("German model")

    sentences = '''
[timer_de]
_minutes = zwei|drei|vier|fünf
Stelle den Timer auf <_minutes>{_minutes} Minuten    
    '''.strip()

    yield TestReport.text("Grammar for training. You can use utf-8 special characters.")
    yield TestReport.code(sentences)

    api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name,'de',sentences))

    yield TestReport.text("Input audio to transcribe:")
    file = File.read(Path(__file__).parent / 'files/timer-de.wav')
    yield TestReport.file(file)

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file, model_name))

    tc.assertEqual('fünf', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('timer_de', result['fsticuffs'][0]['intent']['name'])

    yield TestReport.text("Result:")
    yield TestReport.json(result)



def english_custom(api: BrainBoxApi, tc: TestCase):
    model_name = 'test_english_custom_words'


    yield TestReport.H1("English model with custom words")
    yield TestReport.text("Sometimes Kaldi misses the transcription for this or that word. It can guess it, but the guess is not always good.")

    sentences = '''
[order]
_order = Shi|Ukha|Borsh
I order <_order>{_order}    
        '''.strip()

    yield TestReport.text("Grammar for training. Words `Ukha` and `Borsh` are not in the dictionary")
    yield TestReport.code(sentences)

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name, 'en', sentences))
    tc.assertDictEqual(
        dict(borsh="b 'O r S", ukha="j u k V"),
        result['unknown_words']
    )
    yield TestReport.text("The result of the training:")
    yield TestReport.json(result)

    yield TestReport.text(
        "You can provide your own transcription for the words. "
        "The symbols used for the phonemes are rather peculiar, but Kaldi returns them with examples:"
    )

    phonemes = api.execute(BrainBoxTask.call(RhasspyKaldi).phonemes('en'))
    yield TestReport.code(phonemes)

    custom_words = {
        'shi' : "S i",
        'ukha': "u h 'A",
        'borsh': 'b o r S'
    }
    yield TestReport.text("Custom words' transcription:")
    yield TestReport.json(custom_words)
    result = api.execute(BrainBoxTask.call(RhasspyKaldi).train(model_name, 'en', sentences, custom_words))

    print(result)
    tc.assertEqual(0, len(result['unknown_words']))

    file = File.read(Path(__file__).parent / 'files/ukha.wav')
    yield TestReport.text("Input audio to transcribe:")
    yield TestReport.file(file)

    result = api.execute(BrainBoxTask.call(RhasspyKaldi).transcribe(file, model_name))
    tc.assertEqual('ukha', result['fsticuffs'][0]['entities'][0]['raw_value'])
    tc.assertEqual('order', result['fsticuffs'][0]['intent']['name'])

    yield TestReport.text("Result:")
    yield TestReport.json(result)



