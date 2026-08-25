from dataclasses import dataclass
from pathlib import Path
from chara.common.llm import ILLM, QuestionList
from ...data import Node
from ..scene_engine.interfaces import IQuestionAnswerer


@dataclass
class QuestionsCase:
    scene: Node
    questions: QuestionList

class LLMQuestionAnswerer(IQuestionAnswerer):
    def __init__(self, source: ILLM[QuestionsCase, dict]):
        request = (source
                   .default()
                   .template(Path(__file__).parent / 'llm_question_answerer.jinja')
                   .to_request())
        # The question list varies per scene, so the step reads it off the case.
        self.request = request.edit().questionnaire('questions').to_request()

    def answer(self, current: Node, questions: QuestionList) -> dict:
        return self.request.execute(QuestionsCase(current, questions))
