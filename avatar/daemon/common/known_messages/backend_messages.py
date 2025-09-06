from ....messaging import IMessage
from dataclasses import dataclass


@dataclass
class BackendIdleReport(IMessage):
    is_idle: bool
