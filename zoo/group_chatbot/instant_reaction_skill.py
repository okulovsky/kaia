from typing import *
import telegram as tg
from kaia.eaglesong.drivers.telegram import TgCommand
from abc import ABC, abstractmethod

class TelegramInstantReactionSkill(ABC):
    @abstractmethod
    def execute(self, update: tg.Update) -> Union[None, TgCommand, Iterable[TgCommand]]:
        pass

    def safe_execute(self, update: tg.Update) -> List[TgCommand]:
        result = self.execute(update)
        if result is None:
            return []
        if isinstance(result, TgCommand):
            return [result]
        return list(result)

