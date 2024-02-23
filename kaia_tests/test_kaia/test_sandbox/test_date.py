from unittest import TestCase
from kaia.kaia.skills.date import DateSkill, DateReplies, DateIntents, Weekdays, RelativeDay
from datetime import date, timedelta
from kaia.eaglesong.core import Automaton, Scenario, Return


def d(delta: int):
    return date(2023,10,10)+timedelta(days=delta)

def S():
    return Scenario(lambda: Automaton(DateSkill(lambda: d(0)).run, None))



class TestDate(TestCase):
    def test_no_input(self):
        (
            S()
            .send(DateIntents.question.utter())
            .check(
                DateReplies.answer.utter(weekday=Weekdays.Tuesday, date = d(0)).assertion,
                Return
            )
            .validate()
        )

    def test_with_input(self):
        (
            S()
            .send(DateIntents.question.utter(delta=RelativeDay.The_day_after_tomorrow))
            .check(
                DateReplies.answer.utter(weekday=Weekdays.Thursday, date = d(2)).assertion,
                Return
            )
            .validate()
        )