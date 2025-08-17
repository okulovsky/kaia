from unittest import TestCase
from kaia.skills.date import DateSkill, DateReplies, DateIntents, Weekdays, RelativeDay
from datetime import date, timedelta
from eaglesong.core import Automaton, Scenario, Return
from grammatron import DubParameters


def d(delta: int):
    return date(2023,10,10)+timedelta(days=delta)

def S():
    return Scenario(lambda: Automaton(DateSkill(lambda: d(0)).run, None))



class DateSkillTestCase(TestCase):
    def test_no_input(self):
        (
            S()
            .send(DateIntents.question.utter())
            .check(
                DateReplies.answer.utter(weekday=Weekdays.Tuesday, date = d(0)),
                Return
            )
            .validate()
        )

    def test_with_input(self):
        (
            S()
            .send(DateIntents.question.utter(delta=RelativeDay.The_day_after_tomorrow))
            .check(
                DateReplies.answer.utter(weekday=Weekdays.Thursday, date = d(2)),
                Return
            )
            .validate()
        )

    def test_representation(self):
        u = DateReplies.answer.utter(weekday=Weekdays.Thursday, date = d(2))
        print(u.to_str(DubParameters(False)))