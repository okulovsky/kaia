import uuid
from dataclasses import dataclass
from .word import Word
from brainbox.flow import PromptMappingStepFactory, ListExpansionApplicator, BulletPointParser, Referrer, Prompter
from .question import Question
from .noun_grammar import NounGrammar
from yo_fluq import Query
from brainbox import BrainBox

def _to_comma_list(words):
    return ', '.join(words)

@dataclass
class QuestionBuilder:
    word: Word
    question: str|None = None
    control_answer: str|None = None
    control_answer_index: int|None = None

    def is_success(self):
        return self.control_answer == self.word.word and self.control_answer_index == 0

    @staticmethod
    def export(questions: list['QuestionBuilder']) -> list[Question]:
        questions = [item for item in questions if item.is_success()]
        result = []
        for item in questions:
            if item.control_answer != item.word.word or item.control_answer_index != 0:
                continue
            if item.word.grammar is not NounGrammar:
                continue
            result.append(Question(
                id = str(uuid.uuid4()),
                answer=item.word.word,
                genus=list(item.word.grammar.genus),
                plural=list(item.word.grammar.plural),
                question=item.question,
            ))
        return result


    @staticmethod
    def question_prompt(api: BrainBox.Api):
        o = Referrer[QuestionBuilder]()

        prompt = Prompter(f'''
Sie arbeiten als Deutschlehrer an einer Schule. 
Sie haben beschlossen, eine Quizstunde zu organisieren, in der Sie Fragen stellen und die Schüler antworten. 
Für dieses Quiz müssen Sie sich Wörter ausdenken. 
Die Studierenden sind auf dem Sprachniveau „B1“

Nun müssen Sie sich eine Frage zum Wort „{o.ref.word.word}“ überlegen.

Sie können:

- Beschreiben dieses Word als ob in Wortebuch. Beispielsweise zum Wort „Teller“: "Flaches rundes Geschirr aus Porzellan, Metall oder Plastik, auf dem man Essen legt."

- Beschreiben, wie sich dieses Konzept auf andere bezieht. Beispielsweise zum Wort „Höhle“: „Wo wohnt der Bär“?

- liefern mit diesem Konzept bekannte Fakten. Beispielsweise zum Wort „Apfel“: „Was fiel Newton auf den Kopf“?

Wichtig ist, dass Sie in der Frage selbst weder das Wort „{o.ref.word.word}“ noch Wörter mit derselben Wurzel verwenden.

Wichtig ist außerdem, dass die Frage nur eine Antwort zulässt, nämlich „{o.ref.word.word}“,
und dass keine anderen Wörter geeignet sind,
wie {o.ref.word.similar_words/_to_comma_list}, usw. 

Bitte schreiben Sie 5 solcher Fragen in eine Punkteliste. 
Jeder Listeneintrag muss eine Frage enthalten. 
Schreiben Sie keine zusätzlichen Erklärungen.
        ''')

        return PromptMappingStepFactory(
            api,
            prompt,
            'mistral-small',
            ListExpansionApplicator(o.ref.question),
            BulletPointParser(),
        )

    @staticmethod
    def control_prompt(api: BrainBox.Api):
        o = Referrer[QuestionBuilder]()

        prompt = Prompter(f'''
Sie sind ein Student eines Deutschkurses und erlernen die Sprache auf dem Niveau B1. 
Ihr Lehrer hat beschlossen, im Unterricht ein Quizspiel zu veranstalten. 
Der Lehrer nennt Ihnen ein Thema und stellt Ihnen eine Frage, 
die sich auf ein Nomen bezieht, das mit diesem Thema in Zusammenhang steht.

Sie sollen Ihre Antwortmöglichkeiten in eine Punkteliste schreiben. 
Geben Sie zuerst die wahrscheinlichste Antwort an, dann die weniger wahrscheinlichen.
Jeder Punkt auf der Liste sollte nur ein Wort enthalten – Ihre Antwort auf die Frage, in Singular, ohne Artikel. 
Geben Sie keine Erklärungen oder Begründungen ab.

Beispielsweise lautet die Antwort auf die Frage „Was ist Newton auf den Kopf gefallen?“:

* Apfel

* Birne

Jetzt kommt die Frage: "{o.ref.question}".

Schreiben Sie Ihre Antwort.
''')

        return PromptMappingStepFactory(
            api,
            prompt,
            'mistral-small',
            ListExpansionApplicator(o.ref.control_answer, o.ref.control_answer_index),
            BulletPointParser()
        )
