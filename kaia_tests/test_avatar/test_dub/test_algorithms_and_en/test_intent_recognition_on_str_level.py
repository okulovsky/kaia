from unittest import TestCase
from kaia.avatar.dub.sandbox import Intents
from kaia.avatar.dub.core import TestingTools, RhasspyHandler
from kaia.avatar.dub.core.utils import rhasspy_nlu

class IntentRecognitionTestCase(TestCase):
    def test_intent_recognition(self):
        intents = Intents.get_templates()

        ttools = TestingTools(intents)

        handler = RhasspyHandler(ttools.intents)
        #print(handler.ini_file)

        for sample in ttools.samples:
            sample.against_utterance(handler.parse_string(sample.s))
            sample.recognition_obj = handler.recognitions_
            print(sample.s)
            sample.make_assert(self)





