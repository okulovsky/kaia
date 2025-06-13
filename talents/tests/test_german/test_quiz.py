from unittest import TestCase
from eaglesong import Scenario, Automaton, Return
from talents.german.quiz import Intents, Replies,GermanQuizSkill, Question
from brainbox import MediaLibrary
from avatar import ContentManager, NewContentStrategy, DataClassDataProvider

questions = [
    Question(
        '1',
        'Apfel',
        'Obst',
        ['m'],
        ['Äpfel'],
        'Apfel?',
    ),
    Question(
        '2',
        'Birne',
        'Obst',
        ['f'],
        ['Birnen'],
        'Birne?',
    )
]

def S():
    manager = ContentManager(
        NewContentStrategy(randomize=False),
        DataClassDataProvider(questions, 'id'),
    )

    return Scenario(
        lambda: Automaton(GermanQuizSkill(manager).run_algorithm, None)
    )

class QuizTest(TestCase):
    def test_correct(self):
        (
            S()
            .send('')
            .check(Replies.rules(), 'Obst. Apfel?')
            .send('Der Apfel, die Äpfel')
            .check(Replies.correct(), 'Obst. Birne?')
            .send('Die Birne, die Birnen')
            .check(Replies.correct(), str)
            .send('Genug')
            .check(Replies.summary(fully_correct=100, partially_correct=0), Return)
            .validate()
        )

    def test_wrong(self):
        (
            S()
            .send('')
            .send("Die Birne, die Birnen")
            .check(Replies.incorrect() + 'Der Apfel, die Äpfel', str)
            .validate()
        )

    def test_grammar_and_correct(self):
        (
            S()
            .send('')
            .send('Apfel')
            .check(Replies.incomplete_grammar())
            .send('Der Apfel, die Äpfel')
            .check(Replies.correct(), str)
            .validate()
        )

    def test_grammar_and_incorrect(self):
        (
            S()
            .send('')
            .send('Apfel')
            .check(Replies.incomplete_grammar())
            .send('Das Apfel, die Äpfel')
            .check(Replies.incorrect_grammar() + "Der Apfel, die Äpfel", str)
            .validate()
        )