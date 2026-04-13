from enum import Enum
from dataclasses import dataclass
from .endpoint_decorator import HttpMethod

class ProtocolType(Enum):
    HTTP = 0
    WebSockets = 1


@dataclass
class ProtocolModel:
    type: ProtocolType
    http_method: HttpMethod | None
