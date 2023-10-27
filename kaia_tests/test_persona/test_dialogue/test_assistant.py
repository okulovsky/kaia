from unittest import TestCase
from kaia.persona.sandbox.date import DateSkill, DateReplies, DateIntents
from kaia.persona.sandbox.time import TimeSkill, TimeReplies, TimeIntents
from kaia.persona.sandbox import HomeAssistant, CommonReplies
from kaia.persona.dub.languages.en import *


from kaia.eaglesong.core import Automaton, Scenario, Audio
from kaia.persona.dialogue import UtterancesTranslator
from kaia.persona.dub.core import RhasspyAPI, RhasspyHandler
from datetime import datetime



class AssistantTestCase(TestCase):
    def test_utterance_level(self):
        aut = HomeAssistant([DateSkill(), TimeSkill()])
        (Scenario(lambda: Automaton(aut,None))
         .send(TimeIntents.question.utter())
         .check(TimeReplies.answer.utter().assertion.template_only)
         .send(DateIntents.question.utter())
         .check(DateReplies.answer.utter().assertion.template_only)
         .validate()
        )

    def test_wrong_intent(self):
        aut = HomeAssistant([DateSkill()])
        (Scenario(lambda: Automaton(aut, None))
         .send(TimeIntents.question.utter())
         .check(CommonReplies.not_recognized.utter().assertion)
         .validate()
         )

    def test_text_wrapper(self):
        assistant = HomeAssistant([DateSkill(), TimeSkill(lambda: datetime(2020,1,1,13,45))])
        intents = assistant.get_intents()
        handler = RhasspyHandler(intents)
        aut = UtterancesTranslator(assistant, RhasspyAPI(None, handler))

        (Scenario(lambda: Automaton(aut, None))
         .send('What time is it?')
         .check(TimeReplies.answer.utter(hours=13, minutes=45).to_str())
         .validate()
        )

    def simplify(self, s):
        return s.replace(' ','').replace(',','').replace('.','')



    def test_audio_wrapper(self):
        assistant = HomeAssistant([DateSkill(), TimeSkill(lambda: datetime(2020,1,1,13,45))])
        tc = DubbingTaskCreator()
        sequences = tc.fragment(get_predefined_dubs(), assistant.get_replies(), 'test')
        dubber = DubbingPack(tc.create_mock_fragments(sequences)).create_dubber()

        handler = RhasspyHandler(assistant.get_intents())
        aut = UtterancesTranslator(assistant, RhasspyAPI(None, handler), dubber, True)

        resp = (Scenario(lambda: Automaton(aut, None))
         .send('What time is it?')
         .validate()
         .log[-1].response
        )

        fake_audio = ''.join(resp[0].data).replace(' ','')
        self.assertEqual(
            self.simplify(TimeReplies.answer.utter(hours=13, minutes=45).to_str()),
            self.simplify(fake_audio)
        )





