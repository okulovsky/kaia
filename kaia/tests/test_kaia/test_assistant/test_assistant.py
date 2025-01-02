from unittest import TestCase
from kaia.skills.date import DateSkill, DateReplies, DateIntents
from kaia.skills.time import TimeSkill, TimeReplies, TimeIntents
from kaia.kaia import KaiaAssistant
from kaia.kaia.assistant.automaton_not_found_skill import AutomatonNotFoundReplies
from kaia.kaia.translators import VoiceoverTranslator, RhasspyTextToUtteranceTranslator
from brainbox import BrainBoxApi
from brainbox.deciders import FakeFile
from kaia.avatar import DubbingService, AvatarApi, AvatarSettings, TestTaskGenerator
from eaglesong.core import Automaton, Scenario
from datetime import datetime
import json

class AssistantTestCase(TestCase):
    def test_utterance_level(self):
        aut = KaiaAssistant([DateSkill(), TimeSkill()])
        (Scenario(lambda: Automaton(aut,None))
         .send(TimeIntents.question.utter())
         .check(lambda z: z in TimeReplies.answer)
         .send(DateIntents.question.utter())
         .check(lambda z: z in DateReplies.answer)
         .validate()
        )

    def test_wrong_intent(self):
        aut = KaiaAssistant([DateSkill()])
        (Scenario(lambda: Automaton(aut, None))
         .send(TimeIntents.question.utter())
         .check(AutomatonNotFoundReplies.answer.utter())
         .validate()
         )


    def simplify(self, s):
        return s.replace(' ','').replace(',','').replace('.','')


    def test_audio_wrapper(self):
        with BrainBoxApi.Test([FakeFile()]) as bb_api:
            dubbing_service = DubbingService(
                TestTaskGenerator(),
                bb_api
            )
            with AvatarApi.Test(AvatarSettings(dubbing_task_generator=TestTaskGenerator(), brain_box_api=bb_api)) as avatar_api:
                assistant = KaiaAssistant([DateSkill(), TimeSkill(lambda: datetime(2020, 1, 1, 13, 45))])
                assistant = RhasspyTextToUtteranceTranslator(assistant, assistant.get_intents())
                assistant = VoiceoverTranslator(assistant, avatar_api)

                resp = (Scenario(lambda: Automaton(assistant, None))
                 .send('What time is it?')
                 .validate()
                 .log[-1].response
                )

                self.assertIsInstance(resp[0], str)
                self.assertEqual('It is thirteen hours and forty five minutes.', resp[0])

                self.assertDictEqual(
                    {'voice': 'voice_0', 'text': 'It is thirteen hours and forty five minutes.'},
                    json.loads(resp[1].content)
                )




