from unittest import TestCase
from kaia.eaglesong.core import BotContext, Scenario as S, Routine, Return
from zoo.group_chatbot.skills.skill_stack import SkillStack

class TestRoutine(Routine):
    def __init__(self, words, reply):
        self.words = words
        self.reply = reply

    def get_name(self):
        return self.reply

    def run(self, context: BotContext):
        if context.input in self.words:
            yield self.reply

def get_skill():
    return SkillStack([
        TestRoutine(['A','C'], '1'),
        TestRoutine(['B','C'], '2')
    ])

class SkillStackTestCase(TestCase):
    def test_first_fires(self):
        (
            S(lambda: BotContext(1), get_skill())
            .send('A')
            .check(
                '1',
                Return
            )
            .preview()
        )

    def test_second_fires(self):
        (
            S(lambda: BotContext(1), get_skill())
            .send('B')
            .check(
                '2',
                Return
            )
            .preview()
        )

    def test_only_one_fires(self):
        (
            S(lambda: BotContext(1), get_skill())
            .send('C')
            .check(
                '1',
                Return
            )
            .preview()
        )

    def test_none_fires(self):
        (
            S(lambda: BotContext(1), get_skill())
            .send('D')
            .check(
                Return
            )
            .preview()
        )