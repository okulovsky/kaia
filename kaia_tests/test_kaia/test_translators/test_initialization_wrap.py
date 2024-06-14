from unittest import TestCase
from kaia.kaia.skills.date import DateSkill, DateReplies, DateIntents, Weekdays
from kaia.kaia.skills.time import TimeSkill, TimeIntents, TimeReplies
from kaia.kaia.skills import KaiaTestAssistant
from kaia.kaia.translators import InitializationWrap
from datetime import datetime, date
from kaia.eaglesong.core import Automaton, Scenario, Return
from kaia.kaia.core import Start




def S(supress_outputs):
    dt = lambda: datetime(2023,10,10,13,46)
    assistant = KaiaTestAssistant([DateSkill(dt), TimeSkill(dt)])
    translator = InitializationWrap(assistant, [DateIntents.question.utter()], [TimeIntents.question.utter()], supress_outputs)
    aut = Automaton(translator, None)
    return Scenario(lambda: aut)






class TestDate(TestCase):
    def test_not_first_time(self):
        (
            S(False)
            .send(Start(False))
            .check(DateReplies.answer.utter(weekday=Weekdays.Tuesday, date = date(2023,10,10)).assertion)
            .send(DateIntents.question.utter())
            .check(DateReplies.answer.utter(weekday=Weekdays.Tuesday, date = date(2023,10,10)).assertion)
            .validate()
        )


    def test_first_time(self):
        (
            S(False)
            .send(Start(True))
            .check(
                TimeReplies.answer.utter(hours=13, minutes=46).assertion,
                #DateReplies.answer.utter(weekday=Weekdays.Tuesday, date = date(2023,10,10)).assertion,
            )
            .send(TimeIntents.question.utter())
            .check(TimeReplies.answer.utter(hours=13, minutes=46).assertion)
            .validate()
        )

    def test_supressed_output(self):
        (
            S(True)
            .send(Start(True))
            .check()
            .send(TimeIntents.question.utter())
            .check(TimeReplies.answer.utter(hours=13, minutes=46).assertion)
            .validate()
        )