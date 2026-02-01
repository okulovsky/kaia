from avatar.messaging import StreamClient
from avatar.daemon import NarrationService, State
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class SpeakerIdentificationType(Enum):
    Voice = 0
    Image = 1


@dataclass
class UserIdentification:
    Type = SpeakerIdentificationType

    user: str
    file_id: str
    type: SpeakerIdentificationType
    timestamp: datetime


class KaiaContext:
    def __init__(self, client: StreamClient):
        self._client = client
        self.user: str|None = None
        self.language: str|None = None
        self.previous_identification: UserIdentification|None = None

    def get_client(self):
        return self._client.clone()

    def get_state(self) -> State:
        return self.get_client().run_synchronously(NarrationService.StateRequest(), State)
