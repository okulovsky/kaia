from unittest import TestCase
from kaia.skills.date import DateSkill, DateReplies, DateIntents
from kaia.skills.time import TimeSkill, TimeReplies, TimeIntents
from kaia import KaiaAssistant
from kaia.assistant.automaton_not_found_skill import AutomatonNotFoundReplies
from eaglesong.core import Automaton, Scenario

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


