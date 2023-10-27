from unittest import TestCase
from kaia.eaglesong.core import BotContext, Scenario as S, Return
from zoo.group_chatbot.skills.skill_stack import SkillStack, Automaton

class TestRoutine:
    def __init__(self, words, reply):
        self.words = words
        self.reply = reply

    def get_name(self):
        return self.reply

    def run(self):
        input = yield
        if input in self.words:
            yield self.reply

def get_skill():
    return SkillStack([
        TestRoutine(['A','C'], '1').run,
        TestRoutine(['B','C'], '2').run
    ]).run

class SkillStackTestCase(TestCase):
    def test_first_fires(self):
        (
            S(lambda: Automaton(get_skill(), BotContext(1)))
            .send('A')
            .check(
                '1',
                Return
            )
            .validate()
        )

    def test_second_fires(self):
        (
            S(lambda: Automaton(get_skill(), BotContext(1)))
            .send('B')
            .check(
                '2',
                Return
            )
            .validate()
        )

    def test_only_one_fires(self):
        (
            S(lambda: Automaton(get_skill(), BotContext(1)))
            .send('C')
            .check(
                '1',
                Return
            )
            .validate()
        )

    def test_none_fires(self):
        (
            S(lambda: Automaton(get_skill(), BotContext(1)))
            .send('D')
            .check(
                Return
            )
            .validate()
        )