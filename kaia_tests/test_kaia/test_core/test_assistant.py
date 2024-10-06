from unittest import TestCase
from kaia.kaia.skills.date import DateSkill, DateReplies, DateIntents
from kaia.kaia.skills.time import TimeSkill, TimeReplies, TimeIntents
from kaia.kaia.core import KaiaAssistant
from kaia.kaia.core.automaton_not_found_skill import AutomatonNotFoundReplies
from kaia.kaia.translators import VoiceoverTranslator, RhasspyTextToUtteranceTranslator
from kaia.brainbox import BrainBoxTestApi
from kaia.brainbox.deciders.fake_dub_decider import FakeDubDecider
from kaia.avatar import DubbingService, AvatarApi, AvatarSettings, TestTaskGenerator



from kaia.eaglesong.core import Automaton, Scenario
from datetime import datetime


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
        services = dict(fake_tts=FakeDubDecider())
        with BrainBoxTestApi(services) as bb_api:
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
                    {'voice': 'voice_0', 'text': 'It is thirteen hours and forty five minutes.', 'option_index': 0},
                    resp[1].data
                )




