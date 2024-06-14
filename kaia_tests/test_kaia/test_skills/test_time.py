from unittest import TestCase
from kaia.kaia.skills.time import TimeSkill, TimeReplies, TimeIntents
from datetime import datetime
from kaia.eaglesong.core import Automaton, Scenario, Return

class TimeSkillTestCase(TestCase):
    def test_time(self):
        skill = TimeSkill(lambda: datetime(2020,1,1,13,25))
        (
            Scenario(lambda: Automaton(skill.run, None))
            .send(TimeIntents.question.utter())
            .check(TimeReplies.answer.utter(hours=13, minutes=25).assertion, Return)
            .validate()
        )

