from unittest import TestCase
from kaia.kaia.skills.date import DateSkill, DateReplies, DateIntents
from kaia.kaia.skills.time import TimeSkill, TimeReplies, TimeIntents
from kaia.kaia.skills.kaia_test_assistant import KaiaTestAssistant
from kaia.kaia.skills.automaton_not_found_skill import AutomatonNotFoundReplies
from kaia.kaia.translators import RhasspyInputTranslator, VoiceoverTranslator
from kaia.brainbox import BrainBoxTestApi, BrainBoxTask, BrainBoxTaskPack, DownloadingPostprocessor
from kaia.brainbox.deciders.utils.fake_dub_decider import FakeDubDecider
from kaia.avatar.server import BrainBoxDubbingService, AvatarTestApi, AvatarSettings
from uuid import uuid4
from kaia.infra import FileIO
from kaia.avatar.narrator import DummyNarrator


from kaia.eaglesong.core import Automaton, Scenario
from kaia.avatar.dub.core import RhasspyAPI
from datetime import datetime


def task_generator(s, voice):
    task = BrainBoxTask(str(uuid4()), 'fake_tts', dict(text=s, voice=voice))
    return BrainBoxTaskPack(
        task,
        (),
        DownloadingPostprocessor(take_element_before_downloading=0, opener=FileIO.read_json),
    )


class AssistantTestCase(TestCase):
    def test_utterance_level(self):
        aut = KaiaTestAssistant([DateSkill(), TimeSkill()])
        (Scenario(lambda: Automaton(aut,None))
         .send(TimeIntents.question.utter())
         .check(TimeReplies.answer.utter().assertion.template_only)
         .send(DateIntents.question.utter())
         .check(DateReplies.answer.utter().assertion.template_only)
         .validate()
        )

    def test_wrong_intent(self):
        aut = KaiaTestAssistant([DateSkill()])
        (Scenario(lambda: Automaton(aut, None))
         .send(TimeIntents.question.utter())
         .check(AutomatonNotFoundReplies.answer.utter().assertion)
         .validate()
         )

    def test_text_wrapper(self):
        assistant = KaiaTestAssistant([DateSkill(), TimeSkill(lambda: datetime(2020, 1, 1, 13, 45))])
        intents = assistant.get_intents()
        assistant = RhasspyInputTranslator(assistant, RhasspyAPI(None, intents))
        assistant = VoiceoverTranslator(assistant, None)


        (Scenario(lambda: Automaton(assistant, None))
         .send('What time is it?')
         .check(TimeReplies.answer.utter(hours=13, minutes=45).to_str())
         .validate()
        )

    def simplify(self, s):
        return s.replace(' ','').replace(',','').replace('.','')


    def test_audio_wrapper(self):
        services = dict(fake_tts=FakeDubDecider())
        with BrainBoxTestApi(services) as bb_api:
            dubbing_service = BrainBoxDubbingService(
                task_generator,
                bb_api
            )
            with AvatarTestApi(AvatarSettings(), DummyNarrator('test_voice'), dubbing_service, None) as avatar_api:
                assistant = KaiaTestAssistant([DateSkill(), TimeSkill(lambda: datetime(2020, 1, 1, 13, 45))])
                assistant = RhasspyInputTranslator(assistant, RhasspyAPI(None, assistant.get_intents()))
                assistant = VoiceoverTranslator(assistant, avatar_api)

                resp = (Scenario(lambda: Automaton(assistant, None))
                 .send('What time is it?')
                 .validate()
                 .log[-1].response[0]
                )
                self.assertDictEqual(
                    {'voice': 'test_voice', 'text': 'It is thirteen hours and forty five minutes.', 'option_index': 0},
                    resp.data
                )
                self.assertEqual(
                    'It is thirteen hours and forty five minutes.',
                    resp.text
                )





