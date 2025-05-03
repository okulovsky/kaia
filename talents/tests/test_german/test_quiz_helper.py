from unittest import TestCase
from talents.german.quiz.quiz_helper import QuizHelper, Question, Recognition
from chara.tools.languages import Language

q = Question('1','Apfel','Obst',['m'],['Äpfel'],'Apfel?',)
helper = QuizHelper(Language.German().words_symbols, 'genug', 'schlechte frage', 'pass')

class QuizHelperTestCase(TestCase):
    def check(self, rec_1: Recognition, s):
        self.assertDictEqual(rec_1.__dict__, helper.validate_answer(q, s).__dict__)


    def test_stop(self):
        self.check(
            Recognition(stop=True),
            'Genug!'
        )

    def test_bad_question(self):
        self.check(
            Recognition(bad_question=True),
            'Schlechte Frage!'
        )

    def test_wrong_1(self):
        self.check(
            Recognition(),
            "Birne"
        )

    def test_wrong_2(self):
        self.check(
            Recognition(),
            "Die Birne, die Birnen"
        )

    def test_incomplete(self):
        self.check(
            Recognition(correct_answer=True, incomplete_grammar=True),
            "Apfel"
        )

    def test_article(self):
        self.check(
            Recognition(correct_answer=True, incorrect_article=True),
            "das Apfel, die Äpfel"
        )

    def test_plural(self):
        self.check(
            Recognition(correct_answer=True, incorrect_plural=True),
            "der Apfel, die Apfels"
        )

    def test_all_good(self):
        self.check(
            Recognition(correct_answer=True),
            "der Apfel, die Äpfel"
        )



