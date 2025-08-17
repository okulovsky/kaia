from unittest import TestCase
from kaia.skills.time import TimeSkill, TimeReplies, TimeIntents
from datetime import datetime
from eaglesong.core import Automaton, Scenario, Return

class TimeSkillTestCase(TestCase):
    def test_time(self):
        skill = TimeSkill(lambda: datetime(2020,1,1,13,25))
        (
            Scenario(lambda: Automaton(skill.run, None))
            .send(TimeIntents.question.utter())
            .check(TimeReplies.answer.utter(hours=13, minutes=25), Return)
            .validate()
        )

    def test_template(self):
        s = TimeReplies.answer.utter(hours=13, minutes=45).to_str()
        self.assertEqual('It is 13 hours and 45 minutes.', s)

