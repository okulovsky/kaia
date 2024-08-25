from unittest import TestCase
from kaia.dub.sandbox import Intents
from kaia.dub.rhasspy_utils import RhasspyHandler
from kaia.dub.core import TestingTools
from time import sleep

class IntentRecognitionTestCase(TestCase):
    def test_intent_recognition(self): 
        intents = Intents.get_templates()

        ttools = TestingTools(intents)

        handler = RhasspyHandler(ttools.intents)
        #print(handler.ini_file)

        for sample in ttools.samples:
            sample.against_utterance(handler.parse_string(sample.s))
            sample.recognition_obj = handler.recognitions_
            sleep(0.01)
            sample.make_assert(self)





