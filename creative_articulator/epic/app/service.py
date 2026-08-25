import logging

from .interface import ICreativeArticulator
from ..ai.writing import WritingAi, SelectionCase
from ..model import CreativeArticulatorData, IdToNode
from foundation_kaia.misc import lock

logger = logging.getLogger(__name__)


class CreativeArticulator(ICreativeArticulator):
    def __init__(self,
                 data: CreativeArticulatorData,
                 writing_ai: WritingAi,
                 ):
        self.data = data
        self.writing_ai = writing_ai

    def synchronize(self):
        logger.info("synchronize")
        with lock(self.data.root):
            self.data.synchronize()

    def update(self, id: str, text: str):
        logger.info(f"update: id={id}, {len(text)} char(s)")
        with lock(self.data.root):
            self.data.update(id, text)

    def generate(self, id: str, before_selection: str, selection: str, after_selection: str, action: str) -> str:
        with lock(self.data.root):
            self.data.update(id, before_selection+selection+after_selection)
            case = SelectionCase.parse(self.data.root[IdToNode][id], before_selection, selection, after_selection)
            task = self.writing_ai.create_task(case, action)
        return self.writing_ai.run(task, action)





