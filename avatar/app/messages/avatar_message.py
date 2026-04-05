from dataclasses import dataclass
from foundation_kaia.marshalling_2 import JSON
from ...messaging import Envelop

@dataclass
class AvatarMessage:
    session: str
    content_type: str
    envelop: Envelop
    content: JSON
