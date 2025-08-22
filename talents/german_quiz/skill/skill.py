from typing import Iterable
from grammatron import Template, TemplatesCollection, Utterance, ToStrDub, VariableDub
from kaia import IKaiaSkill, KaiaContext, WhisperOpenMicListen, KaiaSkillBase
from avatar.daemon.common.content_manager import ContentManager, NewContentStrategy, DataClassDataProvider
from eaglesong import Listen, Return, ContextRequest
from chara.tools import Language
from kaia.assistant.kaia_skill import KaiaSkillLanguageSettings
from .quiz_helper import Question, QuizHelper
from yo_fluq import FileIO

class Replies(TemplatesCollection):
    rules = Template("Ich sage dir das Thema, das Rätsel, und du musst antworten: mit dem Artikel und der Pluralform. Los geht's!")
    incorrect = Template("Falsch!")
    correct = Template("Rigtig!")
    incorrect_grammar = Template("Grammatikfehler!")
    incomplete_grammar = Template("Bitte noch ein Artikel und eine Pluralform.")
    bad_article = Template("Falscher Artikel.")
    bad_plural = Template("Falsche Pluralform.")
    bad_article_and_plural = Template("Die ganze Grammatik ist falsch.")
    summary = Template(
        f"{VariableDub('fully_correct')} Prozent der Fragen wurden vollständig richtig beantwortet, weitere {VariableDub('partially_correct')} Prozent wiesen Grammatikfehler auf.",
    )


class Intents(TemplatesCollection):
    start = Template("German quiz")


class GermanQuizSkill(KaiaSkillBase):
    def __init__(self, content_manager: ContentManager[Question], session_length: int = 10):
        self.helper = QuizHelper(Language.German().words_symbols, 'Genug', 'Schlechte Frage', "Keine Ahnung")
        self.manager = content_manager
        self.session_length = session_length
        super().__init__(Intents, Replies)


    def should_start(self, input) -> bool:
        return isinstance(input, Utterance) and input in Intents.start

    def should_proceed(self, input) -> bool:
        return isinstance(input, str) or isinstance(input, Utterance)

    def get_language(self) -> KaiaSkillLanguageSettings:
        return IKaiaSkill.Language.specific('de')

    def run(self):
        yield Replies.rules()
        self.correct_with_grammar = 0
        self.correct_without_grammar = 0
        index = 0

        while index < self.session_length:
            question = self.manager.match().get_content()
            self.manager.feedback(question.id, 'seen')
            yield self.helper.question_to_ask(question)

            status = yield from self.question(question)
            if status == 'stop':
                break
            if status == 'skip':
                continue
            index += 1

        if index!=0:
            fully_correct = int(100*self.correct_with_grammar/index)
            partially_correct = int(100*self.correct_without_grammar/index)
            yield Replies.summary(fully_correct=fully_correct, partially_correct=partially_correct)

    def question(self, question: Question, first_attempt: bool = True) -> str|None:
        whisper_prompt = self.helper.whisper_prompt(question)
        reply = yield WhisperOpenMicListen(whisper_prompt)
        recognition = self.helper.validate_answer(question, reply)
        if recognition.stop:
            return 'stop'
        if recognition.bad_question:
            self.manager.feedback(question.id, 'bad')
            return 'skip'
        if recognition.skip_question:
            yield self.helper.right_answer(question)
            return
        if not recognition.correct_answer:
            yield Replies.incorrect() + self.helper.right_answer(question)
            return
        if recognition.correct_grammar:
            yield Replies.correct()
            self.correct_with_grammar += 1
            return
        if not first_attempt:
            yield Replies.incorrect_grammar() + self.helper.right_answer(question)
            self.correct_without_grammar += 1
            return

        if recognition.incomplete_grammar:
            yield Replies.incomplete_grammar()
        else:
            if recognition.incorrect_plural and recognition.incorrect_article:
                yield Replies.bad_article_and_plural()
            elif recognition.incorrect_plural:
                yield Replies.bad_plural()
            else:
                yield Replies.bad_article()

        final_status = yield from self.question(question, False)
        return final_status

    @staticmethod
    def create_skill(questions_json, questions_log_json, session_length: int = 10):
        question = [
            Question(**d)
            for d in FileIO.read_json(questions_json)
        ]
        manager = ContentManager(
            DataClassDataProvider(question, 'id'),
            questions_log_json,
            NewContentStrategy(),
        )
        return GermanQuizSkill(manager, session_length)







