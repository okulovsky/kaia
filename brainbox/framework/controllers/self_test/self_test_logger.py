from __future__ import annotations
from foundation_kaia.logging import Logger
from typing import TYPE_CHECKING
from .last_call import LastCallDocumentation

if TYPE_CHECKING:
    from brainbox.framework.brainbox import BrainBoxApi

class SelfTestLogger(Logger):
    def last_call(self, api: BrainBoxApi):
        self.log(api.last_call())

logger = SelfTestLogger()